import subprocess

def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,              # allows full shell commands
            capture_output=True,
            text=True
        )

        return {
            "output": result.stdout.strip(),
            "error": result.stderr.strip(),
            "exit_status": result.returncode
        }

    except Exception as e:
        return {
            "output": "",
            "error": str(e),
            "exit_status": -1
        }