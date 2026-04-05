import subprocess

def run_command(host, username, command, key_file=None):
    ssh_command = ["ssh"]

    if key_file:
        ssh_command += ["-i", key_file]

    ssh_command += [f"{username}@{host}", command]

    try:
        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            "output": result.stdout.strip(),
            "error": result.stderr.strip(),
            "exit_status": result.returncode
        }

    except subprocess.TimeoutExpired as e:
        return {
            "output": "",
            "error": "Command timed out",
            "exit_status": -1
        }