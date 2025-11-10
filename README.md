# SubLing 🕷️
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight asynchronous subdomain fuzzing tool, written in Python for subdomain enumeration and web reconnaissance. SubLing efficiently discovers subdomains through concurrent DNS resolution and HTTP/HTTPS probing.

---

### Demo

<img src="https://cdn.imgchest.com/files/eecbdd4a84e1.gif">

---

## ✨ Features

* **Asynchronous Scanning**: Utilizes asyncio for fast, concurrent subdomain enumeration.
* **DNS Resolution**: Efficient DNS checking without external dependencies.
* **HTTP/HTTPS Probing**: Automatically tests discovered subdomains for web services.
* **Flexible Modes**: DNS-only, HTTP-only, or full enumeration modes.
* **Status Code Detection**: Reports HTTP status codes for accessible subdomains.
* **Multiple Output Formats**: Save results to file for further analysis.
* **Beautiful Terminal Output**: Gradient-colored ASCII art and clean result presentation.
* **Auto-Update**: Built-in updater to keep SubLing current with the latest features.

---

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/b3rt1ng/SubLing
    cd SubLing
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    > By default the wordlist used is the seclists one. make sur to have it installed.

3.  **Install system-wide: (optional)**
    ```bash
    python3 install.py
    ```

---

## 💻 Usage

### Basic Command
To run a simple subdomain enumeration with default options:
```bash
python3 main.py example.com
```

### Advanced Example
Run enumeration using a custom wordlist with 200 concurrent workers and save results:
```bash
python3 main.py example.com -w /path/to/wordlist.txt -c 200 -o results.txt
```

### System-Wide Usage
After running the install script, the `subling` command becomes available system-wide from any directory:
```bash
# Basic enumeration
subling example.com

# Advanced enumeration with custom wordlist
subling example.com -w custom-wordlist.txt -c 200

# DNS-only mode (faster)
subling example.com --dns-only

# HTTP-only mode (check web services only)
subling example.com --http-only
```

You can also update the tool from your terminal:
```bash
subling --update
```

### Performance Tips

* **Adjust concurrency**: Use `-c` to set the number of workers. More workers = faster scanning, but be mindful of system resources and rate limiting.
* **DNS-only mode**: Use `--dns-only` for quick DNS enumeration without HTTP checks.
* **Custom timeout**: Adjust `--timeout` based on target responsiveness and your connection speed.
* **Quality wordlists**: Use targeted wordlists for better results. [SecLists](https://github.com/danielmiessler/SecLists) is a great resource.

### All Options
```
usage: subling [-h] [-w FILE] [-c NUM] [--timeout SEC] [-o FILE] [--dns-only] [--http-only] [-t] [--version] [--update] [domain]

SubLing: An asynchronous subdomain fuzzing tool.

positional arguments:
  domain                Target domain (e.g., example.com)

options:
  -h, --help            show this help message and exit
  -w, --wordlist FILE   Path to wordlist (default: SecLists top 5000)
  -c, --concurrency NUM
                        Number of concurrent workers (default: 100)
  --timeout SEC         Timeout in seconds for each request (default: 5)
  -o, --output FILE     Save results to file
  --dns-only            Only perform DNS resolution (skip HTTP checks)
  --http-only           Only check HTTP/HTTPS (skip DNS-only results)
  -t, --transfer        Enable zone transfer detection (AXFR)
  --version             Display the current version of SubLing
  --update              Check for updates and apply them
```

---

## 📝 Wordlists

SubLing works with any text-based wordlist (one subdomain per line). Here are some ressources I like:

* **SecLists**: https://github.com/danielmiessler/SecLists
  * `Discovery/DNS/subdomains-top1million-5000.txt` (default)
  * `Discovery/DNS/subdomains-top1million-20000.txt`
* **Assetnote**: https://wordlists.assetnote.io/
* **jhaddix**: https://gist.github.com/jhaddix/86a06c5dc309d08580a018c66354a056


---

## ⚠️ Disclaimer

This tool is intended for authorized security testing and educational purposes only. Always ensure you have permission before scanning any domain.


---

## 🗺️ Roadmap

- [ ] Recursive subdomain enumeration
- [x] Zone transfer detection
- [ ] Wildcard detection and filtering
- [x] Subdomain takeover detection (W.I.P)

---

**Happy Hunting! 🕷️**
