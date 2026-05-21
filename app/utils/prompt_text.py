import json

from app.core.config import SERVER_HOST, SERVER_PORT, SERVER_USERNAME, SERVER_PASSWORD, GIT_USERNAME, GIT_ACCESS_TOKEN
from app.tools.temp_credential import get_value


def get_banner():
    banner = """
██████╗ ███████╗██╗   ██╗ ██████╗ ██████╗ ██████╗ ███████╗     █████╗ ██╗
██╔══██╗██╔════╝██║   ██║██╔═══██╗██╔══██╗██╔══██╗██╔════╝    ██╔══██╗██║
██║  ██║█████╗  ██║   ██║██║   ██║██████╔╝██████╔╝███████╗    ███████║██║
██║  ██║██╔══╝  ╚██╗ ██╔╝██║   ██║██╔═══╝ ██╔═══╝ ╚════██║    ██╔══██║██║
██████╔╝███████╗ ╚████╔╝ ╚██████╔╝██║     ██║     ███████║    ██║  ██║██║
╚═════╝ ╚══════╝  ╚═══╝   ╚═════╝ ╚═╝     ╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝

                    🚀 D E V O P S   A I 🚀
                 Automation • Deployment • Intelligence
                 """
    return banner

def generate_deployment_prompt():
    prompt = f"""
You are a DevOps automation agent.

Your task is to generate a COMPLETE and VALID deployment plan as a JSON string array of executable commands.

========================
PROJECT DETAILS
========================
Framework: SpringBoot
Repository URL: {get_value('repo_link')}
Domain: {get_value('domain')}

========================
SERVER DETAILS
========================
Host: {get_value('server_host')}
Port: {get_value('server_port')}
User: {get_value('server_user')}
Password: {get_value('server_password')}

========================
REQUIREMENTS
========================

Generate a step-by-step deployment command sequence that includes:

1. Install sshpass (if not already installed)
2. Install dependencies on the server (if not already installed):
   - Docker (verify before install)
   - Git (verify before install)
   - Nginx (verify before install)
   - Certbot (verify before install)

3. Clone the repository
4. Build Docker image 
5. Run Docker container (if not already running then terminate previous and run new)
6. Configure Nginx reverse proxy for the {get_value('domain')}
7. Create/update nginx config file for the {get_value('domain')}
8. Ensure Docker app is exposed on port 8080
9. Setup SSL using Let's Encrypt (only if certificate does not exist)
10. Configure firewall:
   - Allow ports: 22, 80, 443, 8080
   - Do NOT remove SSH access
11. verify any instruction is missing if YES then add those
========================
IDEMPOTENT RULE (VERY IMPORTANT)
========================

Each command must be safe to run multiple times without breaking the system.

Before executing any action:
- Check if already installed:
  command -v docker || install
- Check services:
  systemctl is-active nginx || start
- Check files/folders:
  [ -d repo ] || git clone ...
- Check containers:
  docker ps | grep || run container

Use conditional execution patterns like:
- command || install_command
- test conditions && skip || run

========================
COMMAND FORMAT RULES
========================

- Each command MUST use this SSH format:
  sshpass -p '{get_value('server_password')}' ssh -p {get_value('server_port')} {get_value('server_user')}@{get_value('server_host')} 'command'

- All commands must be:
  - Single-line
  - Self-contained
  - Independently executable

- Use Git credentials in clone:
  https://{get_value('git_username')}:{get_value('git_access_token')}@github.com/...

========================
CRITICAL RULES
========================

- Output MUST be a valid JSON array of OBJECTS matching the schema below
- DO NOT include explanations
- DO NOT include markdown
- DO NOT include extra text
- DO NOT include comments
- DO NOT truncate output
- Ensure valid JSON syntax
- Ensure proper escaping of quotes
- Each command must be idempotent

========================
OUTPUT SCHEMA (MANDATORY)
========================

Each step is an object with EXACTLY these keys:
  - "label":      string, short human-readable name for the step
  - "cmd":        non-empty array of strings, each a fully-formed shell command
  - "verify_cmd": string, a single command that confirms the step succeeded

========================
OUTPUT FORMAT
========================

[
  {{
    "label": "Update apt package index",
    "cmd": [
      "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST 'sudo apt update'"
    ],
    "verify_cmd": "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST 'sudo apt list --upgradable'"
  }},
  {{
    "label": "Install Docker",
    "cmd": [
      "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST 'sudo apt install -y docker.io'",
      "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST 'sudo systemctl enable --now docker'"
    ],
    "verify_cmd": "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST 'docker --version'"
  }}
]

========================
IMPORTANT
========================

Return ONLY the JSON array.
No text before or after.
No explanations.

Now generate the deployment commands.
"""
    return prompt


def generate_result_analysis_prompt(res, workflowDeque):
    prompt = f"""
        You are an AI DevOps assistant.
        
        ========================
        INPUT
        ========================
        Command Execution Result:
        {res}
        
        Expected Workflow:
        {list(workflowDeque)}
        
        ========================
        TASK
        ========================
        Analyze the result and decide next action.
        
        Step 1:
        If "error" is empty/null AND "output" is meaningful → SUCCESS
        → Return:
        []
        
        Step 2:
        If "error" exists → FAILURE
        
        Classify the error:
        - Authentication / SSH / Connection issues
        - Other issues
        
        Step 3:
        ❗ IMPORTANT RULES:
        
        A) If it is Authentication / SSH / Connection related:
        Return ONLY ONE string inside array explaining the issue.
        
        Example:
        [
          "SSH authentication failed. Verify username, password, host, and SSH access."
        ]
        
        B) If it is ANY OTHER error:
        Return ONLY FIX COMMANDS.
        
        ========================
        STRICT REQUIREMENTS FOR FIX COMMANDS
        ========================
        - Output MUST be ONLY an array of commands
        - NO explanations
        - NO text
        - NO markdown
        - NO comments
        - NO descriptions
        
        Each item MUST be a complete executable command.
        
        Preferred commands (examples):
        [
          "apt-get update",
          "pip install package_name"
        ]
        
        If remote execution is needed:
        [
          "sshpass -p 'PASSWORD' ssh USER@HOST 'apt-get update'",
          "sshpass -p 'PASSWORD' ssh USER@HOST 'pip install package_name'"
        ]
        
        ========================
        OUTPUT FORMAT (STRICT JSON ONLY)
        ========================
        
        Case 1 (Success):
        []
        
        Case 2 (Auth issue):
        [
          "single explanation string"
        ]
        
        Case 3 (Other errors):
        [
          "command1",
          "command2"
        ]
        
        ========================
        CRITICAL RULES
        ========================
        - Return ONLY JSON array
        - No explanations at all in command mode
        - No sentences
        - No reasoning
        - No markdown/code blocks
        - No extra characters
        - No trailing commas
        - Use double quotes only
        - Output must be valid JSON
        
        ========================
        FINAL OUTPUT
        ========================
        Return ONLY the JSON array.
        """
    return prompt

def generate_error_fix_prompt(error_block):
    prompt = f"""
You are a DevOps automation agent.

Your task is to analyze failed command executions and return ONLY a valid JSON array of fix steps.

========================
INPUT
========================
{error_block}

Each item contains:
- run_cmd
- error

========================
RULES
========================

1. If ALL errors are empty or null:
Return:
[]

2. If ANY error is related to:
- authentication failure
- wrong host
- wrong password
- SSH connection issue
- permission denied (SSH)

Return EXACTLY one step explaining the auth issue:
[
  {{
    "label": "SSH credentials/connection issue",
    "cmd": ["echo 'Fix SSH credentials or connection (check host, username, password, SSH access)'"],
    "verify_cmd": "echo 'manual intervention required'"
  }}
]

3. For ALL OTHER errors:
- Return ONLY fix steps in the schema below
- Each cmd MUST use this SSH format:
  sshpass -p '{get_value('server_password')}' ssh -p {get_value('server_port')} {get_value('server_user')}@{get_value('server_host')} 'command'

========================
OUTPUT SCHEMA (MANDATORY)
========================

Each step is an object with EXACTLY these keys:
  - "label":      string, short human-readable name for the fix
  - "cmd":        non-empty array of strings, each a fully-formed shell command
  - "verify_cmd": string, a single command that confirms the fix succeeded

========================
OUTPUT FORMAT EXAMPLE
========================

[
  {{
    "label": "Install missing package",
    "cmd": [
      "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST 'sudo apt install -y docker.io'"
    ],
    "verify_cmd": "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST 'docker --version'"
  }}
]

========================
STRICT OUTPUT FORMAT
========================

- Output MUST be valid JSON
- Output MUST be a JSON array of objects matching the schema above (or empty array if no errors)
- NO markdown (no ```json)
- NO explanations
- NO extra text
- NO comments
- NO trailing commas

========================
IMPORTANT
========================

- Response must start with [ and end with ]
- Do not include anything before or after JSON
- Ensure JSON is parseable by json.loads()

Now analyze and return the result.
"""
    return prompt


def get_valid_json_response(call_ai_fn, prompt, max_retries=3):
    """
    call_ai_fn: function that sends prompt to AI and returns response (string)
    prompt: initial prompt
    """

    current_prompt = prompt

    for attempt in range(max_retries):
        response = call_ai_fn(current_prompt)

        try:
            parsed = json.loads(response)
            return parsed

        except json.JSONDecodeError:
            # Re-prompt with correction instruction
            current_prompt = f"""
            Your previous response was invalid JSON.
            
            You MUST return ONLY a valid JSON array of strings.
            
            No explanation. No markdown. No extra text.
            
            Fix and return correct JSON.
            
            Original request:
            {prompt}
            
            Your previous response:
            {response}
            """

    raise Exception("Failed to get valid JSON after retries")


def generate_server_setup_prompt(option: str):
    if option == '1':
        task = 'Install Docker,Docker compose plugin, Nginx, and Certbot on the target Ubuntu server.'
    else:
        raise ValueError("Invalid option selected")

    prompt = f"""
        You are an expert DevOps automation agent.
        
        Your responsibility is to generate a COMPLETE, PRODUCTION-READY, and IDEMPOTENT deployment plan as a VALID JSON ARRAY.
        
        ==================================================
        SERVER INFORMATION
        ==================================================
        Host: {SERVER_HOST}
        Port: {SERVER_PORT}
        Username: {SERVER_USERNAME}
        Password: {SERVER_PASSWORD}
        
        ==================================================
        TASK
        ==================================================
        {task}
        
        ==================================================
        OUTPUT STRUCTURE
        ==================================================
        
        Return ONLY a valid JSON array in the following format:
        
        [
          {{
            "label": "Install Docker",
            "cmd": [
              "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST \\"command\\"",
              "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST \\"command\\""
            ],
            "verify_cmd": "sshpass -p 'PASSWORD' ssh -p PORT USER@HOST \\"command\\""
          }}
        ]
        
        ==================================================
        STRICT REQUIREMENTS
        ==================================================
        
        1. Response MUST be valid JSON.
        2. Return ONLY the JSON array.
        3. No markdown.
        4. No explanations.
        5. No comments.
        6. No extra text before or after JSON.
        7. Every command must be executable independently.
        8. Every command must be a SINGLE LINE.
        9. Commands must be ordered correctly.
        10. Commands must be safe for repeated execution (IDEMPOTENT).
        11. Use Ubuntu-compatible commands only.
        12. Use non-interactive installation flags where applicable.
        13. Use systemctl enable/start only if required.
        14. Include verification commands for every setup section.
        15. Ensure proper JSON escaping.
        
        ==================================================
        SSH COMMAND FORMAT
        ==================================================
        
        Every command MUST strictly use this format:
        
        sshpass -p '{get_value('server_password')}' ssh -o StrictHostKeyChecking=no -p {get_value('server_port')} {get_value('server_user')}@{get_value('server_host')} "command"
        
        ==================================================
        IDEMPOTENCY RULES
        ==================================================
        
        Commands MUST safely support repeated execution.
        
        Preferred patterns:
        
        - command || install_command
        - test_condition && echo "already installed" || install_command
        - systemctl is-enabled service || systemctl enable service
        - docker --version || installation_command
        
        Never generate destructive commands unless absolutely necessary.
        
        ==================================================
        EXPECTED TASKS
        ==================================================
        
        Generate commands for:
        
        1. Updating apt package index
        2. Installing Docker if missing And Installing Docker compose plugin if missing
        3. Enabling and starting Docker
        4. Installing Nginx if missing
        5. Enabling and starting Nginx
        6. Installing Certbot and python3-certbot-nginx if missing
        7. Verifying installations
        
        ==================================================
        FINAL RULE
        ==================================================
        
        Return ONLY the JSON array.
        """
    return prompt


def generate_dockerize_app_deploy_prompt(repo_link: str, enter_domain: str):

    repo_name = repo_link.rstrip("/").split("/")[-1].removesuffix(".git")
    repo_dir = f"/root/{repo_name}"
    auth_repo_url = repo_link.replace(
        "https://github.com/",
        f"https://{GIT_USERNAME}:{GIT_ACCESS_TOKEN}@github.com/",
    )

    prompt = f"""You are a DevOps automation agent. Output ONLY a valid JSON array. No prose. No markdown. No code fences.

TASK: Deploy the Dockerized app at {repo_link} to {enter_domain}.

CONTEXT (use these literal values):
- Repo dir on server: {repo_dir}
- Domain: {enter_domain}
- Clone URL with auth: {auth_repo_url}
- docker, docker compose, nginx, certbot, git are ALREADY INSTALLED — never install, apt-get, snap, or sudo apt.

============================================================
HOW YOUR OUTPUT IS EXECUTED — READ CAREFULLY
============================================================
The runtime takes each "cmd" string and runs it on the remote server as `sshpass ... ssh ... '<your cmd>'`. The single-quote wrapping is added BY THE RUNTIME. You only emit the REMOTE shell command itself. Do NOT include `sshpass`, `ssh`, or any wrapper.

============================================================
JSON RULES (the only rules that matter)
============================================================
1. Each "cmd" entry is a single-string REMOTE shell command. No sshpass, no ssh, no nesting.
2. Inside JSON strings, the ONLY valid escapes are: \\"  \\\\  \\/  \\b  \\f  \\n  \\r  \\t  \\uXXXX. Anything else is invalid JSON.
3. Use bare $ for shell variables and substitutions: $PORT, $(grep ...). NEVER prefix $ with a backslash.
4. For shell strings, use DOUBLE quotes ("..."). Escape inner " as \\" in the JSON.
5. Do NOT use single quotes inside the remote command — they conflict with the runtime's single-quote wrapping. Use double quotes for any shell string you need.

SCHEMA: {{"label": "short name", "cmd": ["<remote shell command>"]}}
Omit "verify_cmd".

============================================================
PRODUCE EXACTLY THESE 4 STEPS, IN ORDER
============================================================

Step 1 — Clone or update {repo_dir}:
    test -d {repo_dir} && git -C {repo_dir} pull || git clone {auth_repo_url} {repo_dir}

Step 2 — Bring up the compose stack. The repo always contains docker-compose.yml (or compose.yaml / compose.yml). Tries multiple docker compose invocations in order. NO install commands. Escape inner " as \\" in JSON:
    cd {repo_dir} && ( [ -f docker-compose.yml ] || [ -f compose.yaml ] || [ -f compose.yml ] || {{ echo "ERROR: no docker-compose.yml / compose.yaml / compose.yml found in {repo_dir}" >&2; exit 1; }} ) && ( docker compose up -d --build || docker-compose up -d --build || /usr/libexec/docker/cli-plugins/docker-compose up -d --build || /usr/lib/docker/cli-plugins/docker-compose up -d --build || {{ echo "ERROR: docker compose did not run. None of the available invocations worked on this server." >&2; exit 1; }} )

Step 3 — Detect the exposed port from the compose file and write a single-line Nginx vhost for {enter_domain}. Escape inner " as \\" in JSON:
    PORT=$(cd {repo_dir} && grep -oP "(?<=- )[0-9]+(?=:)" docker-compose.yml 2>/dev/null || grep -oP "(?<=- )[0-9]+(?=:)" compose.yaml 2>/dev/null || grep -oP "(?<=- )[0-9]+(?=:)" compose.yml 2>/dev/null | head -1) && echo "server {{ listen 80; server_name {enter_domain}; location / {{ proxy_pass http://127.0.0.1:$PORT; }} }}" > /etc/nginx/sites-available/{enter_domain} && ln -sf /etc/nginx/sites-available/{enter_domain} /etc/nginx/sites-enabled/{enter_domain} && nginx -t && systemctl reload nginx

Step 4 — Issue SSL (idempotent; certbot is a no-op if cert already exists):
    certbot --nginx -n --agree-tos -m admin@{enter_domain} -d {enter_domain}

Return ONLY the JSON array containing exactly those 4 steps in that order. Nothing else."""

    return prompt

def generate_static_app_deploy_prompt(enter_domain: str):

    web_root = f"/var/www/{enter_domain}"

    prompt = f"""You are a DevOps automation agent. Output ONLY a valid JSON array. No prose. No markdown. No code fences.

TASK: Deploy a basic static site for {enter_domain}.

CONTEXT (use these literal values):
- Web root on server: {web_root}
- Domain: {enter_domain}
- nginx, certbot are ALREADY INSTALLED — never install, apt-get, snap, or sudo apt.

============================================================
HOW YOUR OUTPUT IS EXECUTED — READ CAREFULLY
============================================================
The runtime takes each "cmd" string and runs it on the remote server as `sshpass ... ssh ... '<your cmd>'`. The single-quote wrapping is added BY THE RUNTIME. You only emit the REMOTE shell command itself. Do NOT include `sshpass`, `ssh`, or any wrapper.

============================================================
JSON RULES
============================================================
1. Each "cmd" entry is a single-string REMOTE shell command. No sshpass, no ssh.
2. Inside JSON strings, valid escapes are ONLY: \\"  \\\\  \\/  \\b  \\f  \\n  \\r  \\t  \\uXXXX.
3. Use DOUBLE quotes for shell strings ("..."). Escape inner " as \\" in JSON.
4. Do NOT use single quotes inside the remote command (they conflict with the runtime wrapper).

SCHEMA: {{"label": "short name", "cmd": ["<remote shell command>"]}}
Omit "verify_cmd".

============================================================
PRODUCE EXACTLY THESE 3 STEPS, IN ORDER
============================================================

Step 1 — Create the web root and a basic index.html (escape the inner " as \\" in JSON):
    mkdir -p {web_root} && echo "<!doctype html><html><body><h1>{enter_domain}</h1></body></html>" > {web_root}/index.html

Step 2 — Write a single-line Nginx vhost serving {web_root}:
    echo "server {{ listen 80; server_name {enter_domain}; root {web_root}; index index.html; }}" > /etc/nginx/sites-available/{enter_domain} && ln -sf /etc/nginx/sites-available/{enter_domain} /etc/nginx/sites-enabled/{enter_domain} && nginx -t && systemctl reload nginx

Step 3 — Issue SSL (idempotent):
    certbot --nginx -n --agree-tos -m admin@{enter_domain} -d {enter_domain}

Return ONLY the JSON array containing exactly those 3 steps in that order. Nothing else."""

    return prompt