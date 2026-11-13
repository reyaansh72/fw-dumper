import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from html import unescape
import re
from urllib.parse import urlparse

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def normalize_url(url):
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.hostname:
        raise ValueError("enter a valid HTTP or HTTPS URL")
    return url.rstrip("/")


def dump(url, dumps_variable, delay=1, output_root="dumps"):

    url = normalize_url(url)
    max_size = 2 * 1024 * 1024

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = Path(output_root) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{YELLOW}Starting dump: {url}{RESET}\n")

    def download(target_url, filename):

        relative_path = Path(filename)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            print(f"{RED}[ERROR] Invalid asset path: {filename}{RESET}")
            return
        filepath = output_dir / relative_path
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            request = urllib.request.Request(
                target_url,
                headers={"User-Agent": "RouterAssetInspector/1.0"}
            )

            with urllib.request.urlopen(request, timeout=10) as response:

                total = response.headers.get("Content-Length")
                total = int(total) if total else None

                if total is not None and total > max_size:
                    print(f"{RED}[ERROR] File too large: {filename}{RESET}")
                    return

                downloaded = 0

                try:
                    with open(filepath, "wb") as file:
                        with tqdm(
                            total=total,
                            desc=filename,
                            unit="B",
                            unit_scale=True,
                            leave=False
                        ) as bar:

                            while True:
                                chunk = response.read(8192)

                                if not chunk:
                                    break

                                downloaded += len(chunk)

                                if downloaded > max_size:
                                    raise ValueError("File exceeds size limit")

                                file.write(chunk)
                                bar.update(len(chunk))

                    print(f"{GREEN}[PULLED] {filename}{RESET}")

                except Exception:
                    filepath.unlink(missing_ok=True)
                    raise

        except urllib.error.HTTPError as error:

            if error.code == 404:
                print(
                    f"{RED}[ERROR] File Not Found 404: {filename}{RESET}"
                )
            else:
                print(
                    f"{RED}[ERROR] Error Code: {error.code} - {filename}{RESET}"
                )

        except Exception as error:
            print(f"{RED}[ERROR] {error}: {filename}{RESET}")

    # Download the default homepage from /
    print(f"{CYAN}Checking default homepage...{RESET}")

    download(url + "/", "homepage.html")
    time.sleep(delay)

    # Download requested frontend assets
    for filename in dumps_variable:

        download(f"{url}/{filename}", filename)
        time.sleep(delay)

    print(f"\n{GREEN}Dump completed!{RESET}")
    print(f"Saved files in: {output_dir}")
    return output_dir


def info(url):

    url = normalize_url(url)

    print(f"\n{CYAN}========== WEBPAGE INFO =========={RESET}\n")
    print(f"{YELLOW}URL:{RESET} {url}")

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "WebPageInspector/1.0"}
        )

        start = time.time()

        with urllib.request.urlopen(request, timeout=10) as response:

            elapsed = round(time.time() - start, 3)

            headers = response.headers
            html = response.read(1024 * 1024).decode(
                "utf-8", errors="replace"
            )

            final_url = response.geturl()
            parsed = urlparse(final_url)

            title = re.search(
                r"<title[^>]*>(.*?)</title>",
                html,
                re.I | re.S
            )

            description = re.search(
                r'<meta\b(?=[^>]*\bname=["\']description["\'])'
                r'(?=[^>]*\bcontent=["\']([^"\']*)["\'])[^>]*>',
                html,
                re.I | re.S
            )

            language = re.search(
                r'<html[^>]*\blang=["\']([^"\']*)',
                html,
                re.I
            )

            print(f"\n{GREEN}HTTP STATUS: {response.status}{RESET}")

            print(f"{CYAN}Host:{RESET} {parsed.hostname}")
            print(f"{CYAN}Scheme:{RESET} {parsed.scheme}")
            print(f"{CYAN}Final URL:{RESET} {final_url}")
            print(f"{CYAN}Server:{RESET} {headers.get('Server', 'Unknown')}")
            print(f"{CYAN}Content-Type:{RESET} {headers.get('Content-Type', 'Unknown')}")
            print(f"{CYAN}Content-Length:{RESET} {headers.get('Content-Length', 'Unknown')}")
            print(f"{CYAN}Response Time:{RESET} {elapsed}s")

            print(f"\n{YELLOW}PAGE METADATA{RESET}")

            print(
                f"Title: {unescape(title.group(1).strip()) if title else 'Not found'}"
            )

            print(
                f"Description: {unescape(description.group(1)) if description else 'Not found'}"
            )

            print(
                f"Language: {language.group(1) if language else 'Not found'}"
            )
            succeeded = True

    except urllib.error.HTTPError as error:
        print(f"{RED}[ERROR] HTTP {error.code}: {error.reason}{RESET}")
        succeeded = False

    except urllib.error.URLError as error:
        print(f"{RED}[ERROR] Connection failed: {error.reason}{RESET}")
        succeeded = False

    except Exception as error:
        print(f"{RED}[ERROR] {error}{RESET}")
        succeeded = False

    print(f"\n{CYAN}=================================={RESET}\n")
    return succeeded