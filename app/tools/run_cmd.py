import subprocess
import os

def run_command(command):
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )

        stdout, stderr = process.communicate()
        exit_status = process.returncode

        # Many tools (docker, git, nginx, certbot) write progress/status to stderr
        # even on success. The exit code is the real signal — only surface stderr
        # as an error when the process actually failed.
        if exit_status == 0:
            return {
                "output": stdout.strip() or stderr.strip(),
                "error": "",
                "exit_status": 0,
            }

        return {
            "output": stdout.strip(),
            "error": stderr.strip(),
            "exit_status": exit_status,
        }

    except Exception as e:
        return {
            "output": "",
            "error": str(e),
            "exit_status": -1,
        }