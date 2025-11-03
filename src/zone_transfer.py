import dns.resolver
import dns.query
import dns.zone
from typing import List, Optional, Set
import asyncio
from .ui import gradient_text, colored_text, GREEN, SPIDER_RED, YELLOW


class ZoneTransferDetector:
    """
    Détecte et exploite les vulnérabilités de zone transfer DNS (AXFR)
    """
    
    def __init__(self, domain: str, timeout: int = 10):
        self.domain = domain
        self.timeout = timeout
        self.nameservers: List[str] = []
        self.vulnerable_ns: List[str] = []
        
    async def get_nameservers(self) -> List[str]:
        """
        Récupère la liste des nameservers pour le domaine cible
        """
        try:
            loop = asyncio.get_event_loop()
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout
            
            # Requête NS pour obtenir les nameservers
            answers = await loop.run_in_executor(
                None,
                lambda: resolver.resolve(self.domain, 'NS')
            )
            
            nameservers = []
            for rdata in answers:
                ns_name = str(rdata.target).rstrip('.')
                
                # Résoudre l'adresse IP du nameserver
                try:
                    ns_answers = await loop.run_in_executor(
                        None,
                        lambda: resolver.resolve(ns_name, 'A')
                    )
                    for ns_ip in ns_answers:
                        nameservers.append(str(ns_ip.address))
                except Exception:
                    # Si résolution IP échoue, on garde le nom
                    nameservers.append(ns_name)
            
            self.nameservers = nameservers
            return nameservers
            
        except dns.resolver.NXDOMAIN:
            return []
        except dns.resolver.NoAnswer:
            return []
        except dns.resolver.NoNameservers:
            return []
        except Exception:
            return []
    
    async def attempt_axfr(self, nameserver: str) -> Optional[Set[str]]:
        """
        Tente un zone transfer AXFR sur un nameserver spécifique
        Retourne un set de sous-domaines si succès, None sinon
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Tentative de zone transfer
            zone = await loop.run_in_executor(
                None,
                lambda: dns.zone.from_xfr(
                    dns.query.xfr(nameserver, self.domain, timeout=self.timeout)
                )
            )
            
            # Extraction des sous-domaines
            subdomains = set()
            for name, node in zone.nodes.items():
                subdomain = str(name)
                if subdomain == '@':
                    subdomains.add(self.domain)
                elif subdomain:
                    full_domain = f"{subdomain}.{self.domain}"
                    subdomains.add(full_domain)
            
            self.vulnerable_ns.append(nameserver)
            return subdomains
            
        except dns.exception.FormError:
            # Le serveur a refusé le zone transfer (comportement normal)
            return None
        except dns.exception.Timeout:
            return None
        except ConnectionRefusedError:
            return None
        except Exception:
            return None
    
    async def check_all_nameservers(self) -> Optional[Set[str]]:
        """
        Teste tous les nameservers pour détecter une vulnérabilité de zone transfer
        Retourne tous les sous-domaines trouvés ou None
        """
        if not self.nameservers:
            await self.get_nameservers()
        
        if not self.nameservers:
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
        """
        Affiche un rapport détaillé de la vulnérabilité détectée
        """
        print(gradient_text("\n" + "="*60))
        print(colored_text("⚠️  CRITICAL SECURITY ISSUE DETECTED!", SPIDER_RED))
        print(gradient_text("="*60))
        
        print(colored_text("\n🚨 Zone Transfer Vulnerability Found!", YELLOW))
        print(f"\n   Domain: {colored_text(self.domain, YELLOW)}")
        print(f"   Vulnerable NS: {colored_text(', '.join(self.vulnerable_ns), SPIDER_RED)}")
        print(f"   Exposed records: {colored_text(len(subdomains), SPIDER_RED)}")
        
        print(gradient_text("\n📋 Recommendation:"))
        print("   Configure your DNS servers to restrict zone transfers")
        print("   Only allow transfers from authorized secondary nameservers")
        
        print(gradient_text("\n✅ All subdomains retrieved via zone transfer!"))
        print(gradient_text("="*60 + "\n"))


async def check_zone_transfer_vulnerability(domain: str, timeout: int = 10) -> Optional[Set[str]]:
    """
    Fonction helper pour vérifier rapidement si un domaine est vulnérable au zone transfer
    
    Args:
        domain: Le domaine cible
        timeout: Timeout en secondes pour chaque requête
        
    Returns:
        Set de sous-domaines si vulnérable, None sinon
    """
    detector = ZoneTransferDetector(domain, timeout)
    subdomains = await detector.check_all_nameservers()
    
    if subdomains:
        detector.print_vulnerability_report(subdomains)
    
    return subdomains