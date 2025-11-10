import dns.resolver
import dns.query
import dns.zone
from typing import List, Optional, Set
import asyncio
from .ui import gradient_text, colored_text, print_report_box, GREEN, SPIDER_RED, YELLOW


class ZoneTransferDetector:
    
    def __init__(self, domain: str, timeout: int = 10):
        self.domain = domain
        self.timeout = timeout
        self.nameservers: List[str] = []
        self.vulnerable_ns: List[str] = []
        
    async def get_nameservers(self) -> List[str]:
        try:
            loop = asyncio.get_event_loop()
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout
            
            answers = await loop.run_in_executor(
                None,
                lambda: resolver.resolve(self.domain, 'NS')
            )
            
            nameservers = []
            for rdata in answers:
                ns_name = str(rdata.target).rstrip('.')
                
                try:
                    ns_answers = await loop.run_in_executor(
                        None,
                        lambda name=ns_name: resolver.resolve(name, 'A')
                    )
                    for ns_ip in ns_answers:
                        nameservers.append(str(ns_ip.address))
                except Exception:
                    nameservers.append(ns_name)
            
            self.nameservers = nameservers
            return nameservers
            
        except dns.resolver.NXDOMAIN:
            print(colored_text("   ❌ Domain does not exist (NXDOMAIN)", SPIDER_RED))
            return []
        except dns.resolver.NoAnswer:
            print(colored_text("   ❌ No NS records found", YELLOW))
            return []
        except dns.resolver.NoNameservers:
            print(colored_text("   ❌ No nameservers available", SPIDER_RED))
            return []
        except Exception as e:
            print(colored_text(f"   ❌ Error resolving nameservers: {e}", SPIDER_RED))
            return []
    
    async def attempt_axfr(self, nameserver: str) -> Optional[Set[str]]:
        try:
            loop = asyncio.get_event_loop()
            
            zone = await loop.run_in_executor(
                None,
                lambda: dns.zone.from_xfr(
                    dns.query.xfr(nameserver, self.domain, timeout=self.timeout)
                )
            )
            
            subdomains = set()
            for name, node in zone.nodes.items():
                subdomain = str(name)
                if subdomain == '@':
                    subdomains.add(self.domain)
                elif subdomain:
                    full_domain = f"{subdomain}.{self.domain}".rstrip('.')
                    subdomains.add(full_domain)
            
            self.vulnerable_ns.append(nameserver)
            return subdomains
        except:
            return None
    
    async def check_all_nameservers(self) -> Optional[Set[str]]:
        if not self.nameservers:
            await self.get_nameservers()
        
        if not self.nameservers:
            print(colored_text("\n❌ No nameservers found for zone transfer test", SPIDER_RED))
            return None
        
        print(gradient_text(f"\n🔍 Testing zone transfer on {len(self.nameservers)} nameserver(s)..."))
        
        all_subdomains = set()
        
        for ns in self.nameservers:
            print(f"   • Trying AXFR on {ns}...", end=" ", flush=True)
            
            subdomains = await self.attempt_axfr(ns)
            
            if subdomains:
                print(colored_text("✓ VULNERABLE!", SPIDER_RED))
                all_subdomains.update(subdomains)
            else:
                print(colored_text("✗ Protected", GREEN))
        
        if all_subdomains:
            return all_subdomains
        
        return None
    
    def print_vulnerability_report(self, subdomains: Set[str]):
        vulnerability_data = {
            "Status": colored_text("⚠️  CRITICAL VULNERABILITY", SPIDER_RED),
            "Domain": colored_text(self.domain, YELLOW),
            "Vulnerable NS": colored_text(', '.join(self.vulnerable_ns), SPIDER_RED),
            "Exposed Records": colored_text(str(len(subdomains)), SPIDER_RED),
            "Risk Level": colored_text("HIGH", SPIDER_RED)
        }
        
        print_report_box("🚨 Zone Transfer Vulnerability Detected", vulnerability_data)
        
        recommendations_data = {
            "Action 1": "Configure DNS servers to restrict zone transfers",
            "Action 2": "Only allow transfers from authorized secondary nameservers",
            "Action 3": "Use TSIG (Transaction Signature) for authentication",
            "Action 4": "Regularly audit DNS security configurations"
        }
        
        print_report_box("📋 Security Recommendations", recommendations_data)
        
        print(gradient_text("\n✅ All subdomains retrieved via zone transfer!\n"))


async def check_zone_transfer_vulnerability(domain: str, timeout: int = 10) -> Optional[Set[str]]:
    detector = ZoneTransferDetector(domain, timeout)
    subdomains = await detector.check_all_nameservers()
    
    if subdomains:
        detector.print_vulnerability_report(subdomains)
    
    return subdomains