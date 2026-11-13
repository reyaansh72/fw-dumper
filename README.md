# FW Dumper

FW Dumper is a command-line utility for inspecting a router or IoT device's web interface and downloading a predefined set of common frontend assets (HTML, CSS, JavaScript, images, fonts, and metadata files). Use it only with devices you own or have explicit permission to inspect.

## Requirements

- Python 3.8 or newer
- The packages listed in `requirements.txt`

Install dependencies from the project directory:

```bash
python -m pip install -r requirements.txt
```

## Commands

Run commands from the project directory with `python app.py`.

### Start a dump

```bash
python app.py start-dump http://192.168.1.1
```

The command displays available page and HTTP metadata, then downloads the default asset list. Files are saved in a timestamped folder under `dumps/`; a ZIP containing that dump is created alongside the folder.

Options:

```text
--delay SECONDS   Wait between requests (default: 1)
--no-zip          Skip creating the ZIP archive
```

For example:

```bash
python app.py start-dump https://192.168.1.1 --delay 0.5
```

### List saved dumps

```bash
python app.py ls-dump
```

Shows each dump's timestamp ID, number of downloaded files, and whether a ZIP archive exists.

### Delete a dump

```bash
python app.py delete-dump 20261113_143012_123456
```

The command asks for confirmation before deleting the selected dump and its matching ZIP archive. Add `--yes` to skip the prompt:

```bash
python app.py delete-dump 20261113_143012_123456 --yes
```

Use the dump ID printed by `ls-dump`.

### Inspect a device

```bash
python app.py info http://192.168.1.1
```

Displays HTTP response details and basic page metadata without downloading the asset list.

## Help

```bash
python app.py --help
python app.py start-dump --help
```

## How it works

- The asset list is defined in `app.py`.
- Download and page-inspection logic lives in `lib/dumper.py`.
- Each run gets its own timestamped directory under `dumps/`.
- Individual downloads are limited to 2 MiB.

The tool requests only the predefined paths; it does not crawl the site or bypass authentication. Devices may require authentication or use different asset paths, in which case some requests may fail.

## Responsible use

Only run FW Dumper against devices you own or are explicitly authorized to assess. The user is responsible for ensuring that their use complies with applicable law and network policies.
