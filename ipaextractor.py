#!/usr/bin/env python3
import getpass
import os
import sys
import time
import stat
import posixpath

try:
    import paramiko
except Exception:
    print("Missing dependency: paramiko. Run: pip install -r requirements.txt")
    sys.exit(1)


def ssh_connect(host, username, password, port=22, timeout=10):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, port=port, username=username, password=password, timeout=timeout)
        return client
    except Exception as e:
        return None, str(e)


def run_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode(errors='ignore')
    err = stderr.read().decode(errors='ignore')
    return out.strip(), err.strip()


def sh_quote(s):
    return "'" + s.replace("'", "'\\''") + "'"


def search_remote(ssh, name):
    roots = ['/home', '/opt', '/var/www', '/usr/local', '/usr/share', '/etc']
    found = set()
    for root in roots:
        cmd_files = f"find {root} -type f -iname \"*{name}*\" 2>/dev/null || true"
        out, err = run_cmd(ssh, cmd_files)
        for line in out.splitlines():
            if line:
                found.add(line.strip())

        cmd_dirs = f"find {root} -type d -iname \"*{name}*\" 2>/dev/null || true"
        out, err = run_cmd(ssh, cmd_dirs)
        for line in out.splitlines():
            if line:
                found.add(line.strip())

        cmd_grep = f"grep -RIl --binary-files=without-match -e {sh_quote(name)} {root} 2>/dev/null || true"
        out, err = run_cmd(ssh, cmd_grep)
        for line in out.splitlines():
            if line:
                found.add(line.strip())

    return sorted(found)


def sftp_mkdir_local(path):
    os.makedirs(path, exist_ok=True)


def sftp_download_recursive(sftp, remote_path, local_base):
    try:
        attr = sftp.stat(remote_path)
    except IOError:
        return [f"Remote path not found: {remote_path}"]
    messages = []
    if stat.S_ISDIR(attr.st_mode):
        for entry in sftp.listdir_attr(remote_path):
            remote_child = posixpath.join(remote_path, entry.filename)
            local_child = os.path.join(local_base, remote_child.lstrip('/'))
            if stat.S_ISDIR(entry.st_mode):
                sftp_mkdir_local(local_child)
                messages += sftp_download_recursive(sftp, remote_child, local_base)
            else:
                sftp_mkdir_local(os.path.dirname(local_child))
                try:
                    sftp.get(remote_child, local_child)
                    messages.append(f"Downloaded: {remote_child} -> {local_child}")
                except Exception as e:
                    messages.append(f"Failed to download {remote_child}: {e}")
    else:
        local_path = os.path.join(local_base, remote_path.lstrip('/'))
        sftp_mkdir_local(os.path.dirname(local_path))
        try:
            sftp.get(remote_path, local_path)
            messages.append(f"Downloaded: {remote_path} -> {local_path}")
        except Exception as e:
            messages.append(f"Failed to download {remote_path}: {e}")
    return messages


def main():
    host = input('Target IP: ').strip()
    username = input('Username: ').strip()
    password = getpass.getpass('Password: ')

    if not host or not username:
        print('Host and username are required')
        return

    print('Connecting to SSH...')
    res = ssh_connect(host, username, password)
    if isinstance(res, tuple):
        ssh, err = res
    else:
        ssh = res
        err = None

    if ssh is None:
        print('Could not connect via SSH. Please provide correct details or check connection.')
        if err:
            print('Error:', err)
        return

    print('SSH connected.')

    out, err = run_cmd(ssh, 'whoami && id && groups || true')
    print('Privileges and identity:')
    print(out)
    if err:
        print('Errors:', err)

    pkg = input('Package name (press Enter or type no to skip): ').strip()
    if pkg == '' or pkg.lower() == 'no':
        app = input('Application name: ').strip()
    else:
        app = ''

    print('Provided:')
    print('Package:', pkg)
    print('Application:', app)

    search_term = pkg if pkg else app
    if not search_term:
        print('No package or application name provided. Skipping search.')
        ssh.close()
        return

    print(f"Searching remote for '{search_term}' (this may take a while)...")
    found = search_remote(ssh, search_term)
    if not found:
        print('No matching files or folders found.')
    else:
        print('Found locations:')
        for p in found:
            print(p)

    proceed = input('Proceed to SFTP download step? (yes/no): ').strip().lower()
    if proceed not in ('yes', 'y'):
        print('Thank you.')
        ssh.close()
        return

    try:
        sftp = ssh.open_sftp()
    except Exception as e:
        print('SFTP connection failed. Please check connection or credentials.')
        print('Error:', e)
        ssh.close()
        return

    base_name = pkg if pkg else (app if app else f'download_{int(time.time())}')
    local_base = os.path.join(os.getcwd(), base_name)
    os.makedirs(local_base, exist_ok=True)

    all_messages = []
    if not found:
        print('Nothing to download.')
    else:
        for remote in found:
            msg = sftp_download_recursive(sftp, remote, local_base)
            all_messages += msg

    print('Download results:')
    for m in all_messages:
        print(m)

    print('Files downloaded to:', local_base)
    print('Thanks.')
    sftp.close()
    ssh.close()


if __name__ == '__main__':
    main()
