import subprocess

def run_command(command):
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        return {
            "output": stdout.strip(),
            "error": stderr.strip(),
        }

    except Exception as e:
        return {
            "output": "",
            "error": str(e),
            "exit_status": -1
        }