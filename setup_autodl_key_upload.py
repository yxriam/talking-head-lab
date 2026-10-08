import os
import pathlib
import stat
import sys

import paramiko


HOST = "connect.bjb1.seetacloud.com"
PORT = 36228
USER = "root"
KEY_NAME = "codex_autodl_36228"
LOCAL_REF = r"D:\project\data\reference.m4a"
REMOTE_REF = "/root/chatterbox_refs/reference.m4a"


def run(client, command, timeout=30):
    _, stdout, stderr = client.exec_command(command, timeout=timeout)
    rc = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    if rc != 0:
        raise RuntimeError(f"command failed rc={rc}: {command}\n{err}")
    return out, err


def main():
    password = os.environ["AUTODL_PASS"]
    ssh_dir = pathlib.Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    key_path = ssh_dir / KEY_NAME
    pub_path = ssh_dir / f"{KEY_NAME}.pub"

    if key_path.exists():
        key = paramiko.RSAKey.from_private_key_file(str(key_path))
    else:
        key = paramiko.RSAKey.generate(4096)
        key.write_private_key_file(str(key_path))
    pub = f"{key.get_name()} {key.get_base64()} {KEY_NAME}"
    pub_path.write_text(pub + "\n", encoding="ascii")
    try:
        os.chmod(key_path, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        pass

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST,
        port=PORT,
        username=USER,
        password=password,
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    escaped_pub = pub.replace("'", "'\\''")
    run(
        client,
        "mkdir -p ~/.ssh /root/chatterbox_refs && chmod 700 ~/.ssh && "
        "touch ~/.ssh/authorized_keys && "
        f"grep -qxF '{escaped_pub}' ~/.ssh/authorized_keys || "
        f"echo '{escaped_pub}' >> ~/.ssh/authorized_keys; "
        "chmod 600 ~/.ssh/authorized_keys",
    )
    sftp = client.open_sftp()
    sftp.put(LOCAL_REF, REMOTE_REF)
    sftp.close()
    client.close()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST,
        port=PORT,
        username=USER,
        key_filename=str(key_path),
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    out, err = run(
        client,
        "whoami && hostname && ls -lh /root/chatterbox_refs/reference.m4a && "
        "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true",
    )
    client.close()
    print(f"KEY={key_path}")
    print(out, end="")
    if err.strip():
        print(err, file=sys.stderr)


if __name__ == "__main__":
    main()
