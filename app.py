import argparse
import math
import re
import shlex
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from lib import dumper


DEFAULT_ASSETS = [
    "index.html",
    "login.html",
    "home.html",
    "status.html",
    "dashboard.html",
    "error.html",
    "404.html",
    "js/index.js",
    "js/main.js",
    "js/app.js",
    "js/common.js",
    "js/jquery.js",
    "js/jquery.min.js",
    "js/jquery-1.8.0.min.js",
    "js/mis.js",
    "js/textValidations.js",
    "js/loadingStatus.js",
    "js/excanvas.js",
    "js/bootstrap.js",
    "js/bootstrap.min.js",
    "js/script.js",
    "js/functions.js",
    "js/validation.js",
    "css/style.css",
    "css/theme.css",
    "css/main.css",
    "css/common.css",
    "css/login.css",
    "css/responsive.css",
    "css/bootstrap.css",
    "css/bootstrap.min.css",
    "images/logo.png",
    "images/loginLogo.png",
    "images/favicon.ico",
    "images/background.png",
    "images/banner.png",
    "images/loader.gif",
    "images/loading.gif",
    "images/play.gif",
    "fonts/Montserrat-Regular.ttf",
    "fonts/Roboto-Regular.ttf",
    "fonts/fontawesome-webfont.woff",
    "robots.txt",
    "sitemap.xml",
    "manifest.json",
]

PROJECT_ROOT = Path(__file__).resolve().parent
DUMPS_DIR = PROJECT_ROOT / "dumps"
DUMP_ID_PATTERN = re.compile(r"^\d{8}_\d{6}(?:_\d{6})?$")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Inspect a device web interface and collect its common frontend assets."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    start_parser = commands.add_parser(
        "start-dump", help="inspect a device and download its common web assets"
    )
    start_parser.add_argument("url", help="device URL, e.g. http://192.168.1.1")
    start_parser.add_argument(
        "--delay",
        type=float,
        default=1,
        help="seconds to wait between requests (default: 1)",
    )
    start_parser.add_argument(
        "--no-zip",
        action="store_true",
        help="do not create a ZIP archive of the downloaded files",
    )

    commands.add_parser("ls-dump", help="list saved dumps")

    delete_parser = commands.add_parser("delete-dump", help="delete a saved dump")
    delete_parser.add_argument("dump_id", help="dump ID shown by ls-dump")
    delete_parser.add_argument(
        "--yes", action="store_true", help="delete without asking for confirmation"
    )

    info_parser = commands.add_parser("info", help="show device page and HTTP metadata")
    info_parser.add_argument("url", help="device URL, e.g. http://192.168.1.1")

    return parser


def run_shell():
    print("FW Dumper interactive shell. Type 'help' for commands or 'exit' to quit.")
    while True:
        try:
            line = input("fw-dumper> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            return 0
        if line.lower() in ("help", "?"):
            build_parser().print_help()
            print("\nShell commands: help, exit, quit")
            continue

        try:
            command_args = shlex.split(line)
        except ValueError as error:
            print(f"Could not parse command: {error}", file=sys.stderr)
            continue

        try:
            main(command_args)
        except SystemExit as error:
            if error.code not in (0, None):
                continue


def create_archive(dump_dir, url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname or "device"
    safe_hostname = re.sub(r"[^A-Za-z0-9_-]+", "_", hostname).strip("_") or "device"
    archive_path = dump_dir.parent / f"{safe_hostname}_{dump_dir.name}.zip"

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(dump_dir.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(dump_dir))

    return archive_path


def list_dumps():
    dump_dirs = sorted(
        (
            path
            for path in DUMPS_DIR.iterdir()
            if path.is_dir() and DUMP_ID_PATTERN.fullmatch(path.name)
        ),
        reverse=True,
    ) if DUMPS_DIR.exists() else []

    if not dump_dirs:
        print("No dumps found.")
        return

    print(f"{'DUMP ID':<24} {'FILES':>5}  {'ARCHIVE'}")
    for dump_dir in dump_dirs:
        file_count = sum(1 for path in dump_dir.rglob("*") if path.is_file())
        has_archive = any(DUMPS_DIR.glob(f"*_{dump_dir.name}.zip"))
        print(
            f"{dump_dir.name:<24} {file_count:>5}  "
            f"{'yes' if has_archive else 'no'}"
        )


def delete_dump(dump_id, skip_confirmation=False):
    if not DUMP_ID_PATTERN.fullmatch(dump_id):
        print("Invalid dump ID. Use an ID shown by ls-dump.", file=sys.stderr)
        return False

    dump_dir = DUMPS_DIR / dump_id
    if not dump_dir.is_dir() or dump_dir.resolve().parent != DUMPS_DIR.resolve():
        print(f"Dump not found: {dump_id}", file=sys.stderr)
        return False

    if not skip_confirmation:
        answer = input(f"Delete dump {dump_id} and its archive, if present? [y/N] ")
        if answer.strip().lower() != "y":
            print("Deletion cancelled.")
            return False

    shutil.rmtree(dump_dir)
    for archive_path in DUMPS_DIR.glob(f"*_{dump_id}.zip"):
        if archive_path.is_file():
            archive_path.unlink()

    print(f"Deleted dump {dump_id}.")
    return True


def run_start_dump(url, delay, no_zip):
    if not math.isfinite(delay) or delay < 0:
        print("--delay must be a finite number zero or greater.", file=sys.stderr)
        return 2

    try:
        normalized_url = dumper.normalize_url(url)
    except ValueError as error:
        print(f"Invalid URL: {error}", file=sys.stderr)
        return 2

    print("Inspecting device...")
    dumper.info(normalized_url)

    print(f"Starting dump from {normalized_url}")
    dump_dir = dumper.dump(
        normalized_url,
        DEFAULT_ASSETS,
        delay=delay,
        output_root=DUMPS_DIR,
    )

    if not no_zip:
        archive_path = create_archive(dump_dir, normalized_url)
        print(f"Created archive: {archive_path}")
    print(f"Dump saved to: {dump_dir}")
    return 0


def main(argv=None):
    if argv is None and len(sys.argv) == 1:
        return run_shell()

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "start-dump":
        return run_start_dump(args.url, args.delay, args.no_zip)
    if args.command == "ls-dump":
        list_dumps()
        return 0
    if args.command == "delete-dump":
        return 0 if delete_dump(args.dump_id, args.yes) else 1
    if args.command == "info":
        try:
            url = dumper.normalize_url(args.url)
        except ValueError as error:
            print(f"Invalid URL: {error}", file=sys.stderr)
            return 2
        return 0 if dumper.info(url) else 1

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
