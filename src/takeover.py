import asyncio
import aiohttp
import dns.resolver
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from .ui import gradient_text, colored_text, print_report_box, GREEN, SPIDER_RED, YELLOW, LIGHT_BLUE

def load_takeover_signatures():
    json_path = Path(__file__).parent.parent / "data" / "takeover_signatures.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"Takeover signatures file not found: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        signatures = json.load(f)
    
    if not isinstance(signatures, dict):
        raise ValueError("Invalid format in takeover_signatures.json")
    
    # Optional: Validate required fields
    for service, sig in signatures.items():
        if not all(key in sig for key in ["cname", "response", "fingerprint"]):
            raise ValueError(f"Invalid signature for {service}: missing required fields")
    
    return signatures

class SubdomainTakeoverDetector:
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.vulnerable_subdomains: List[Dict] = []
        self.checked_count = 0
        self.takeover_signatures = load_takeover_signatures()
        
    async def get_cname_records(self, subdomain: str) -> List[str]:
        try:
            loop = asyncio.get_event_loop()
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout
            
            answers = await loop.run_in_executor(
                None,
                lambda: resolver.resolve(subdomain, 'CNAME')
            )
            
            cnames = [str(rdata.target).rstrip('.') for rdata in answers]
            return cnames
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return []
        except Exception:
            return []
    
    async def check_http_response(self, session: aiohttp.ClientSession, subdomain: str) -> Optional[Tuple[int, str]]:
        for protocol in ("https", "http"):
            url = f"{protocol}://{subdomain}"
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ssl=False,
                    allow_redirects=True,
                ) as response:
                    content = await response.text()
                    return (response.status, content)
            except (aiohttp.ClientError, asyncio.TimeoutError):
                continue
            except Exception:
                continue
        return None
    
    def match_signature(self, cnames: List[str], response_data: Optional[Tuple[int, str]]) -> Optional[Dict]:
        if not cnames:
            return None
        
        for service_name, signature in self.takeover_signatures.items():
            cname_match = False
            matched_cname = None
            for cname in cnames:
                for sig_cname in signature["cname"]:
                    if sig_cname in cname.lower():
                        cname_match = True
                        matched_cname = cname
                        break
                if cname_match:
                    break
            
            if not cname_match:
                continue
            
            if response_data:
                status, content = response_data
                content_lower = content.lower()
                
                for error_string in signature["response"]:
                    if error_string.lower() in content_lower:
                        return {
                            "service": service_name,
                            "cname": matched_cname,
                            "status": status,
                            "fingerprint": signature["fingerprint"]
                        }
        
        return None
    
    async def check_subdomain(
        self,
        session: aiohttp.ClientSession,
        subdomain: str
    ) -> Optional[Dict]:
        try:
            cnames = await self.get_cname_records(subdomain)
            
            if not cnames:
                return None
            
            response_data = await self.check_http_response(session, subdomain)
            
            match = self.match_signature(cnames, response_data)
            
            if match:
                return {
                    "subdomain": subdomain,
                    "service": match["service"],
                    "cname": match["cname"],
                    "status": match.get("status", "N/A"),
                    "fingerprint": match["fingerprint"]
                }
            
            return None
            
        except Exception:
            return None
    
    async def scan_subdomains(
        self,
        subdomains: Dict[str, Tuple[Optional[str], Optional[int]]],
        workers: int = 20
    ):
        print(gradient_text(f"\n🔍 Checking {len(subdomains)} subdomain(s) for takeover vulnerabilities...\n"))
        
        connector = aiohttp.TCPConnector(limit=workers, ssl=False)
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config
        ) as session:
            tasks = []
            for subdomain in subdomains.keys():
                task = self.check_subdomain(session, subdomain)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                self.checked_count += 1
                if isinstance(result, dict) and result:
                    self.vulnerable_subdomains.append(result)
                    self.print_vulnerability(result)
        
        print(gradient_text(f"\n✨ Takeover scan completed. Checked {self.checked_count} subdomain(s).\n"))
    
    def print_vulnerability(self, vuln: Dict):
        subdomain_colored = gradient_text(vuln["subdomain"], start_color=LIGHT_BLUE, end_color=YELLOW)
        service_colored = colored_text(vuln["service"], SPIDER_RED)
        cname_colored = colored_text(vuln["cname"], YELLOW)
        
        print(f"  🚨 {subdomain_colored}")
        print(f"     Service: {service_colored} | CNAME: {cname_colored} | Status: {vuln['status']}")
    
    def print_summary_report(self):
        if not self.vulnerable_subdomains:
            summary_data = {
                "Total Checked": str(self.checked_count),
                "Vulnerabilities": colored_text("0", GREEN),
                "Status": colored_text("✓ No takeover vulnerabilities detected", GREEN)
            }
            print_report_box("🛡️  Subdomain Takeover Scan Results", summary_data)
            return
        
        vuln_by_service = {}
        for vuln in self.vulnerable_subdomains:
            service = vuln["service"]
            vuln_by_service[service] = vuln_by_service.get(service, 0) + 1
        
        summary_data = {
            "Total Checked": str(self.checked_count),
            "Vulnerabilities Found": colored_text(str(len(self.vulnerable_subdomains)), SPIDER_RED),
            "Risk Level": colored_text("CRITICAL", SPIDER_RED)
        }
        
        print_report_box("🚨 Subdomain Takeover Vulnerabilities Detected", summary_data)
        
        service_data = {}
        for service, count in vuln_by_service.items():
            service_data[service] = colored_text(f"{count} vulnerable subdomain(s)", SPIDER_RED)
        
        print_report_box("📊 Vulnerabilities by Service", service_data)
        
        recommendations_data = {
            "Action 1": "Remove or update DNS records pointing to unclaimed services",
            "Action 2": "Claim the services if they belong to your organization",
            "Action 3": "Monitor subdomains regularly for takeover risks",
            "Action 4": "Implement automated subdomain inventory management"
        }
        
        print_report_box("📋 Security Recommendations", recommendations_data)


async def check_subdomain_takeover(
    subdomains: Dict[str, Tuple[Optional[str], Optional[int]]],
    timeout: int = 10,
    workers: int = 20
) -> List[Dict]:
    if not subdomains:
        print(gradient_text("\n⚠️  No subdomains to check for takeover vulnerabilities.\n"))
        return []
    
    detector = SubdomainTakeoverDetector(timeout)
    await detector.scan_subdomains(subdomains, workers)
    detector.print_summary_report()
    
    return detector.vulnerable_subdomains