from typing import List, Dict, Optional, Tuple


def load_wordlist(filepath: str) -> List[str]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(f"Wordlist not found: {filepath}")
    
    if not words:
        raise ValueError(f"Wordlist is empty: {filepath}")
    
    return words


def save_results(
    output_file: str,
    found_subdomains: Dict[str, Tuple[Optional[str], Optional[int], Optional[str]]]
) -> None:
    try:
        with open(output_file, 'w') as f:
            for subdomain, (proto, status, ip) in sorted(found_subdomains.items()):
                if proto:
                    f.write(f"{subdomain} [{proto}] [{status}]\n")
                else:
                    if ip:
                        f.write(f"{subdomain} [DNS] [{ip}]\n")
                    else:
                        f.write(f"{subdomain} [DNS]\n")
    except Exception as e:
        raise IOError(f"Error saving results: {e}")


def validate_domain(domain: str) -> bool:
    if not domain or not isinstance(domain, str):
        return False
    
    if ' ' in domain or '.' not in domain or len(domain) > 253:
        return False
    
    return True