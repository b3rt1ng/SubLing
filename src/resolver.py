import asyncio
import socket
from typing import Optional, Tuple
import aiohttp


async def get_ip_address(subdomain: str, timeout: int = 5) -> Optional[str]:
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                socket.getaddrinfo,
                subdomain,
                None,
                socket.AF_INET
            ),
            timeout=timeout
        )
        if result:
            return result[0][4][0]
        return None
    except (socket.gaierror, asyncio.TimeoutError, Exception):
        return None


async def check_dns(subdomain: str, timeout: int = 5) -> bool:
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                socket.getaddrinfo,
                subdomain,
                None,
                socket.AF_INET
            ),
            timeout=timeout
        )
        return bool(result)
    except (socket.gaierror, asyncio.TimeoutError, Exception):
        return False


async def check_http(
    session: aiohttp.ClientSession,
    subdomain: str,
    timeout: int = 5
) -> Optional[Tuple[str, int, Optional[int]]]:
    for protocol in ("https", "http"):
        url = f"{protocol}://{subdomain}"
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                ssl=False,
                allow_redirects=True,
            ) as response:
                size = None
                content_length = response.headers.get('Content-Length')
                if content_length:
                    try:
                        size = int(content_length)
                    except ValueError:
                        pass
                
                return (protocol, response.status, size)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            continue
        except Exception:
            continue
    return None


async def get_content_size(
    session: aiohttp.ClientSession,
    subdomain: str,
    protocol: str,
    timeout: int = 5
) -> Optional[int]:
    url = f"{protocol}://{subdomain}"
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=timeout),
            ssl=False,
            allow_redirects=True,
        ) as response:
            content_length = response.headers.get('Content-Length')
            if content_length:
                try:
                    return int(content_length)
                except ValueError:
                    pass
            
            try:
                content = await asyncio.wait_for(
                    response.read(),
                    timeout=min(timeout, 3)
                )
                return len(content)
            except asyncio.TimeoutError:
                return None
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None
    except Exception:
        return None