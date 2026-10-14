# iPA Extracter

A lightweight Python utility for connecting to a remote Linux host over SSH, locating application-related files or folders by package or app name, and optionally downloading the matching content over SFTP.

This project is designed for legitimate system administration, software recovery, or authorized security assessment workflows where you need to search a target system for app artifacts and copy them locally.

## Features

- SSH authentication to a remote host
- Collects the current user identity, privilege information, and group membership
- Searches common system paths for files, directories, and text matches related to a package or app name
- Supports recursive SFTP download of matching remote paths
- Creates a local folder named after the package or application for saved results

## Repository contents

- `ipaextractor.py` — main script
- `requirements.txt` — Python dependency list
- `README.md` — project documentation

## Requirements

- Python 3.8+
- Access to a remote host with SSH enabled
- Valid username and password (or equivalent SSH-based credentials)
- Network access to the target host

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run the script:

```bash
python ipaextractor.py
```

You will be prompted for:

- Target IP or hostname
- SSH username
- Password
- Package name, or leave blank to use an application name instead

The script will:

1. Connect to the host over SSH
2. Display the current user and privilege details
3. Search common filesystem locations such as `/home`, `/opt`, `/var/www`, `/usr/local`, `/usr/share`, and `/etc`
4. Print matching files and folders
5. Ask whether to continue with SFTP download
6. Download matching remote content into a local folder in the current working directory

## Example workflow

```text
Target IP: 192.168.1.50
Username: admin
Password: ********
Package name (press Enter or type no to skip): com.example.app

Searching remote for 'com.example.app'...
Found locations:
/home/user/app
/opt/com.example.app

Proceed to SFTP download step? (yes/no): yes
```

Downloaded files will be placed in a folder such as:

```text
./com.example.app/
```

## Important notes

- The script searches well-known system directories and may take time depending on the target host.
- Some servers may restrict SSH access or SFTP operations.
- Use only with explicit authorization for the target system.
- This repository does not currently specify a license.

## Disclaimer

This tool is intended for authorized use only. You are responsible for ensuring you have permission to access and download data from any remote system you target.
