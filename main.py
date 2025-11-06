#!/usr/bin/env python3
import argparse
import sys
import os
import asyncio
import time
from pathlib import Path
from urllib.parse import urlparse
import re

real_script_path = Path(os.path.realpath(__file__))
project_root = real_script_path.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.core import SubdomainFuzzer
from src.ui import display_art, gradient_text, print_report_box
from src.utils import save_results, validate_domain
from src.updater import update_command

try:
    import tldextract
except Exception:
    print("❌ Le module 'tldextract' est requis mais n'est pas installé.")
    print("Installe-le avec :")
    print("    pip install tldextract")
    sys.exit(1)


def normalize_registered_domain(raw: str) -> str:
    if not raw:
        raise ValueError("empty target")

    raw = raw.strip()

    parsed = urlparse(raw if "://" in raw else "http://" + raw)
    hostname = parsed.hostname or raw

    if not hostname:
        raise ValueError(f"Impossible d'extraire le host depuis: {raw}")

    hostname = hostname.rstrip(".")

    ext = tldextract.extract(hostname)
    if ext.domain and ext.suffix:
        return f"{ext.domain}.{ext.suffix}"

    return hostname.lstrip("www.")


def extract_hostname(raw: str) -> str:
    if not raw:
        raise ValueError("empty target")

    raw = raw.strip()
    parsed = urlparse(raw if "://" in raw else "http://" + raw)
    hostname = parsed.hostname or raw
    if not hostname:
        raise ValueError(f"Impossible d'extraire le host depuis: {raw}")
    return hostname.rstrip(".")


def simple_hostname_validation(hostname: str) -> bool:
    if len(hostname) > 253:
        return False
    labels = hostname.split(".")
    label_re = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?$")
    for label in labels:
        if len(label) == 0 or len(label) > 63:
            return False
        if not label_re.match(label):
            return False
    return True


def get_current_version():
    version_file = project_root / "version.txt"
    try:
        if version_file.exists():
            return version_file.read_text().strip()
        return "unknown"
    except Exception as e:
        print(f"Warning: Could not read version file: {e}", file=sys.stderr)
        return "unknown"


async def main():
    parser = argparse.ArgumentParser(
        description="SubLing: An asynchronous subdomain fuzzing tool.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "domain",
        nargs='?',
        default=None,
        help="Target domain or URL (e.g., example.com or https://example.com/path)"
    )
    parser.add_argument(
        "-w", "--wordlist",
        type=str,
        default="/usr/share/seclists/Discovery/DNS/n0kovo_subdomains.txt",
        metavar="FILE",
        help="Path to wordlist (default: SecLists top 5000)"
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=100,
        metavar="NUM",
        help="Number of concurrent workers (default: 100)"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=5,
        metavar="SEC",
        help="Timeout in seconds for each request (default: 5)"
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Save results to file"
    )
    parser.add_argument(
        "--dns-only",
        action="store_true",
        help="Only perform DNS resolution (skip HTTP checks)"
    )
    parser.add_argument(
        "--http-only",
        action="store_true",
        help="Only check HTTP/HTTPS (skip DNS-only results)"
    )
    parser.add_argument(
        "--keep-host",
        action="store_true",
        help="Keep the full host from the input (e.g. fuzz subdomains of some.web.site.com) instead of the registered domain (site.com)."
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Display the current version of SubLing"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Check for updates and apply them"
    )
    
    args = parser.parse_args()
    current_version = get_current_version()

    if args.version:
        print(f"🕷️  SubLing version: {gradient_text(current_version)}")
        sys.exit(0)

    if args.update:
        update_command(project_root)
        sys.exit(0)
    
    if not args.domain:
        parser.error("domain argument is required (Use --help for more info)")
        sys.exit(1)

    raw_input = args.domain

    if args.keep_host:
        try:
            target = extract_hostname(raw_input)
        except ValueError as e:
            print(gradient_text(f"❌ Target invalid: {e}"))
            sys.exit(1)

        if not simple_hostname_validation(target):
            print(gradient_text(f"❌ Invalid hostname format: {target} (input: {raw_input})"))
            sys.exit(1)
        target_label = "Target Host"
    else:
        try:
            target = normalize_registered_domain(raw_input)
        except ValueError as e:
            print(gradient_text(f"❌ Target invalid: {e}"))
            sys.exit(1)

        if not validate_domain(target):
            print(gradient_text(f"❌ Invalid domain format after normalization: {target} (input: {raw_input})"))
            sys.exit(1)
        target_label = "Target Domain"

    display_art()
    
    config_data = {
        "Input": raw_input,
        target_label: target,
        "Version": current_version,
        "Wordlist": args.wordlist,
        "Workers": args.concurrency,
        "Timeout": f"{args.timeout}s",
        "Mode": "DNS Only" if args.dns_only else "HTTP Only" if args.http_only else "Full"
    }
    
    if args.output:
        config_data["Output File"] = args.output
    
    print_report_box("SubLing Configuration", config_data)
    print(gradient_text("🔍 Starting subdomain fuzzing.\n"))
    
    fuzzer = SubdomainFuzzer(
        domain=target,
        wordlist=args.wordlist,
        workers=args.concurrency,
        timeout=args.timeout,
        dns_only=args.dns_only,
        http_only=args.http_only
    )
    
    start = time.time()
    await fuzzer.run()
    end = time.time()
    
    elapsed = end - start
    print(gradient_text(f"\n✨ Fuzzing completed in {elapsed:.2f} seconds."))

    if args.output and fuzzer.found_subdomains:
        print(f"💾 Saving results to {args.output}...")
        try:
            save_results(args.output, fuzzer.found_subdomains)
            print(gradient_text("✅ Results saved successfully!"))
        except IOError as e:
            print(gradient_text(f"❌ {e}"))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(gradient_text("\n🛑 Fuzzing cancelled by user. Exiting."))
