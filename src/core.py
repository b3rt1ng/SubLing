import asyncio
import time
from typing import Dict, Optional, Tuple
import aiohttp

from .resolver import check_dns, check_http, get_ip_address, get_content_size
from .utils import load_wordlist
from .ui import (
    print_progress_bar,
    gradient_text,
    whole_line,
    colorize_status,
    colored_text,
    format_bytes,
    LIGHT_BLUE,
    DARK_BLUE,
    GREY,
)


class SubdomainFuzzer:
    
    def __init__(
        self,
        domain: str,
        wordlist: str,
        workers: int = 50,
        timeout: int = 5,
        dns_only: bool = False,
        http_only: bool = False,
    ):
        self.domain = domain
        self.wordlist = wordlist
        self.workers = max(1, int(workers))
        self.timeout = timeout
        self.dns_only = dns_only
        self.http_only = http_only

        self.found_subdomains: Dict[str, Tuple[Optional[str], Optional[int], Optional[str], Optional[int]]] = {}
        self.checked_count = 0
        self.total_words = 0
        self.header_printed = False
        self.start_time = None

        self.print_lock = asyncio.Lock()
        self.status_update_interval = max(1, self.workers // 10)

    def print_header(self):
        if not self.header_printed:
            print(gradient_text("\n------- Found Subdomains ------"))
            self.header_printed = True

    def print_footer(self):
        print(gradient_text("-------------------------------\n"))

    async def display_found(
        self,
        subdomain: str,
        proto: Optional[str],
        status: Optional[int],
        ip: Optional[str],
        size: Optional[int],
        update: bool = False
    ):
        async with self.print_lock:
            if update:
                print("\033[F", end="")
            
            print(f"\r{whole_line()}\r", end="")

            if not self.header_printed:
                self.print_header()

            subdomain_colored = gradient_text(
                subdomain,
                start_color=LIGHT_BLUE,
                end_color=DARK_BLUE
            )

            base = ""
            if proto:
                status_colored = colorize_status(status)
                base = f"  {subdomain_colored} : [{proto}] {status_colored}"
            else:
                base = f"  {subdomain_colored} : [DNS]"
            
            if ip:
                ip_colored = colored_text(ip, GREY)
                base += f" [{ip_colored}]"
            
            if size is not None:
                size_formatted = format_bytes(size)
                size_colored = colored_text(size_formatted, GREY)
                base += f" [{size_colored}]"
            
            print(base)

    async def process_worker(
        self,
        queue: asyncio.Queue,
        session: aiohttp.ClientSession
    ):
        while True:
            try:
                word = await queue.get()
                if word is None:
                    queue.task_done()
                    break

                subdomain = f"{word.strip()}.{self.domain}"
                self.checked_count += 1

                if (self.checked_count % self.status_update_interval) == 0 or self.checked_count == 1:
                    async with self.print_lock:
                        print_progress_bar(
                            self.checked_count,
                            self.total_words,
                            self.start_time
                        )

                ip = None
                size = None
                
                try:
                    if self.http_only:
                        result = await check_http(session, subdomain, self.timeout)
                        if result:
                            proto, status, size = result
                            ip = await get_ip_address(subdomain, self.timeout)
                            
                            if size is not None:
                                self.found_subdomains[subdomain] = (proto, status, ip, size)
                                await self.display_found(subdomain, proto, status, ip, size, update=False)
                            else:
                                self.found_subdomains[subdomain] = (proto, status, ip, None)
                                await self.display_found(subdomain, proto, status, ip, None, update=False)
                                size = await get_content_size(session, subdomain, proto, self.timeout)
                                if size is not None:
                                    self.found_subdomains[subdomain] = (proto, status, ip, size)
                                    await self.display_found(subdomain, proto, status, ip, size, update=True)
                    else:
                        dns_exists = await check_dns(subdomain, self.timeout)
                        if dns_exists:
                            ip = await get_ip_address(subdomain, self.timeout)
                            if self.dns_only:
                                self.found_subdomains[subdomain] = (None, None, ip, None)
                                await self.display_found(subdomain, None, None, ip, None, update=False)
                            else:
                                result = await check_http(session, subdomain, self.timeout)
                                if result:
                                    proto, status, size = result
                                    if size is not None:
                                        self.found_subdomains[subdomain] = (proto, status, ip, size)
                                        await self.display_found(subdomain, proto, status, ip, size, update=False)
                                    else:
                                        self.found_subdomains[subdomain] = (proto, status, ip, None)
                                        await self.display_found(subdomain, proto, status, ip, None, update=False)
                                        size = await get_content_size(session, subdomain, proto, self.timeout)
                                        if size is not None:
                                            self.found_subdomains[subdomain] = (proto, status, ip, size)
                                            await self.display_found(subdomain, proto, status, ip, size, update=True)
                                else:
                                    self.found_subdomains[subdomain] = (None, None, ip, None)
                                    await self.display_found(subdomain, None, None, ip, None, update=False)
                except Exception:
                    pass
                finally:
                    queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception:
                queue.task_done()
                break

    async def run(self):
        try:
            words = load_wordlist(self.wordlist)
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return
        except ValueError as e:
            print(f"❌ {e}")
            return

        self.total_words = len(words)
        self.start_time = time.time()

        connector = aiohttp.TCPConnector(limit=self.workers, ssl=False)
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)

        queue = asyncio.Queue(maxsize=self.workers * 2)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config
        ) as session:
            workers = [
                asyncio.create_task(self.process_worker(queue, session))
                for _ in range(self.workers)
            ]

            try:
                for word in words:
                    await queue.put(word)

                for _ in range(self.workers):
                    await queue.put(None)

                await queue.join()
                
            except KeyboardInterrupt:
                pass
            finally:
                for task in workers:
                    if not task.done():
                        task.cancel()
                
                await asyncio.gather(*workers, return_exceptions=True)

        print(f"\r{whole_line()}\r", end="")
        if self.header_printed:
            self.print_footer()