# FW Dumper

FW Dumper is a command-line utility for inspecting a router or IoT device's web interface and downloading a predefined set of common frontend assets (HTML, CSS, JavaScript, images, fonts, and metadata files). Use it only with devices you own or have explicit permission to inspect.

## Requirements

- Python 3.8 or newer
- The packages listed in `requirements.txt`

Install dependencies from the project directory:

```bash
python -m pip install -r requirements.txt
```

## Interactive CLI

Start the shell from the project directory:

```bash
python app.py
```

You will see a `fw-dumper>` prompt. Enter commands there and run as many as needed without restarting the program:

```text
fw-dumper> start-dump http://192.168.1.1
fw-dumper> ls-dump
fw-dumper> info http://192.168.1.1
fw-dumper> delete-dump 20261113_143012_123456
fw-dumper> exit
```

Type `help` inside the shell to list available commands. Use `exit` or `quit` to leave.

### Start a dump

The command displays available page and HTTP metadata, then downloads the default asset list. Files are saved in a timestamped folder under `dumps/`; a ZIP containing that dump is created alongside the folder.

Options:

```text
--delay SECONDS   Wait between requests (default: 1)
--no-zip          Skip creating the ZIP archive
```

For example, at the `fw-dumper>` prompt:

```bash
start-dump https://192.168.1.1 --delay 0.5
```

### List saved dumps

```text
fw-dumper> ls-dump
```

Shows each dump's timestamp ID, number of downloaded files, and whether a ZIP archive exists.

### Delete a dump

```text
fw-dumper> delete-dump 20261113_143012_123456
```

The command asks for confirmation before deleting the selected dump and its matching ZIP archive. Add `--yes` to skip the prompt:

```text
fw-dumper> delete-dump 20261113_143012_123456 --yes
```

Use the dump ID printed by `ls-dump`.

### Inspect a device

```text
fw-dumper> info http://192.168.1.1
```

Displays HTTP response details and basic page metadata without downloading the asset list.

## Help

```text
fw-dumper> help
```

For scripts or one-off invocations, the same commands can still be passed directly:

```bash
python app.py ls-dump
python app.py start-dump http://192.168.1.1 --no-zip
python app.py --help
```

## How it works

- The asset list is defined in `app.py`.
- Download and page-inspection logic lives in `lib/dumper.py`.
- Each run gets its own timestamped directory under `dumps/`.
- Individual downloads are limited to 2 MiB.

The tool requests only the predefined paths; it does not crawl the site or bypass authentication. Devices may require authentication or use different asset paths, in which case some requests may fail.

## Responsible use

Only run FW Dumper against devices you own or are explicitly authorized to assess. The user is responsible for ensuring that their use complies with applicable law and network policies.
