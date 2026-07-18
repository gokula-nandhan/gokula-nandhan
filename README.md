# Gokula Nandhan Profile SVG Generator

This repository generates a terminal-style profile card as `dark.svg` and `light.svg`.

## What it does

- Builds SVG profile cards with GitHub stats and contact links.
- Pulls live GitHub data when the script runs.
- Regenerates the output SVG files from the Python template.

## Files

- `generate_profile.py` generates `dark.svg` and `light.svg`.
- `update.py` is a small entry point that runs the generator.
- `photo_to_ascii.py` can convert `images/avatar.png` into `portrait.txt`.
- `images/avatar.png` is the source image used by the ASCII converter.

## Requirements

- Python 3.9+
- `requests`
- `Pillow`

## Setup

Install the Python packages:

```bash
pip install requests pillow
```

## Usage

Generate the SVG files:

```bash
python generate_profile.py
```

Or run the updater:

```bash
python update.py
```

If you want to regenerate the ASCII portrait file, run:

```bash
python photo_to_ascii.py
```

## Notes

- The scripts may use `GITHUB_TOKEN` or `ACCESS_TOKEN` from your environment for better API limits.
- The generated SVG files are overwritten each time the generator runs.
