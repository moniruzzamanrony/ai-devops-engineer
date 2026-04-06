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

        # 🚫 Filter unwanted warning lines
        def is_noise(line):
            noise_keywords = [
                "WARNING:",
                "warning:",
                "perl: warning",
                "locale:",
                "debconf:",
                "dpkg-preconfigure",
                "No containers need to be restarted",
                "No user sessions are running",
                "No VM guests are running",
                "Restarting services",
                "Service restarts being deferred"
            ]
            return any(keyword in line for keyword in noise_keywords)

        clean_error = "\n".join(
            line for line in stderr.splitlines()
            if not is_noise(line)
        )

        return {
            "output": stdout.strip(),
            "error": clean_error.strip(),
        }

    except Exception as e:
        return {
            "output": "",
            "error": str(e),
            "exit_status": -1
        }