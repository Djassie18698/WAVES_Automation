import os
import requests
import subprocess
import time
import json
import random
import string
from pathlib import Path

# === CONFIG ===
ROOT = Path(__file__).parent.resolve()
SSH_KEY = Path.home() / ".ssh" / "surfspotkey"
SSH_PUB = SSH_KEY.with_suffix(".pub")
INVENTORY = ROOT / "inventory.ini"
PLAYBOOK = ROOT / "setup_vm.yml"
IDFINDER = ROOT / "IDFinder_basic.py"
DATA_DIR = ROOT / "data"
LOG_FILE = DATA_DIR / "automation_log.txt"
DATA_DIR.mkdir(exist_ok=True)

LAST_COMMIT_FILE = DATA_DIR / "last_commit.txt"
WORKSPACE_TEMPLATE = DATA_DIR / "workspace_config_surftest_no_storage.json"
NAME_LOG_FILE = DATA_DIR / "last_workspace_names.txt"
LOOKUP_JSON = DATA_DIR / "workspace_ip_lookup.json"

# === Prompt credentials ===
ssh_user = input("SSH username for VM: ").strip()
github_user = input("GitHub username: ").strip()
github_repo = input("GitHub repo (user/repo): ").strip()
github_token = input("GitHub token: ").strip()
surf_api_key = input("SURF API key: ").strip()

# === Logging ===
def log(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    full_msg = f"{timestamp} {msg}"
    print(full_msg)
    with open(LOG_FILE, "a") as f:
        f.write(full_msg + "\n")

# === SSH key handling ===
def ensure_ssh_key():
    if SSH_KEY.exists() and SSH_PUB.exists():
        log("✅ SSH key exists.")
        return
    log("Generating new SSH key: surfspotkey")
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-f", str(SSH_KEY), "-N", ""])
    with open(SSH_PUB, "r") as f:
        log("Public key (upload to SURFspot):")
        log(f.read())
    input("Press Enter after uploading your key...")

# === GitHub commit monitoring ===
def get_latest_commit():
    url = f"https://api.github.com/repos/{github_repo}/commits"
    headers = {"Authorization": f"token {github_token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()[0]["sha"]
    except Exception as e:
        log(f"GitHub check failed: {e}")
        return None

def read_last_commit():
    if LAST_COMMIT_FILE.exists():
        return LAST_COMMIT_FILE.read_text().strip()
    return ""

def write_last_commit(commit):
    with open(LAST_COMMIT_FILE, "w") as f:
        f.write(commit)

# === SURF Workspace creation ===
def generate_random_name(prefix="surftest", length=5):
    return f"{prefix}-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_workspace():
    headers = {
        "accept": "application/json;Compute",
        "authorization": surf_api_key,
        "Content-Type": "application/json;Compute"
    }
    with open(WORKSPACE_TEMPLATE, "r") as f:
        payload = json.load(f)
    name = generate_random_name()
    payload["meta"]["host_name"] = name
    payload["name"] = name
    response = requests.post("https://gw.live.surfresearchcloud.nl/v1/workspace/workspaces/", headers=headers, json=payload)
    if response.status_code in [200, 201, 202]:
        with open(NAME_LOG_FILE, "w") as f:
            f.write(name)
        log(f"Workspace '{name}' created.")
        return True
    else:
        log(f"Workspace creation failed: {response.status_code}\n{response.text}")
        return False

# === IP Finder ===
def run_idfinder():
    log("Running IDFinder...")
    env = os.environ.copy()
    env["ANSIBLE_SSH_USER"] = ssh_user
    result = subprocess.run(["python3", str(IDFINDER)], env=env)
    if result.returncode == 0:
        log("IDFinder completed.")
    else:
        log("IDFinder failed.")
    return result.returncode == 0

# === IP extraction ===
def get_last_ip():
    if not INVENTORY.exists():
        log("inventory.ini not found.")
        return None
    with open(INVENTORY, "r") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.strip() == "[myhosts]" and i + 1 < len(lines):
            ip = lines[i + 1].split()[0]
            log(f"Extracted IP: {ip}")
            return ip
    log("No IP found in inventory.")
    return None

# === Delete workspace ===
def delete_workspace_by_id():
    if not LOOKUP_JSON.exists():
        log("Cannot delete workspace: workspace_ip_lookup.json not found.")
        return
    with open(LOOKUP_JSON) as f:
        data = json.load(f)
        workspace_id = data.get("workspace_id")
    if not workspace_id:
        log("Cannot delete workspace: ID missing in JSON.")
        return
    url = f"https://gw.live.surfresearchcloud.nl/v1/workspace/workspaces/{workspace_id}/"
    headers = {
        "accept": "*/*",
        "authorization": surf_api_key
    }
    response = requests.delete(url, headers=headers)
    if response.status_code in [200, 204]:
        log(f"🗑Workspace {workspace_id} deleted successfully.")
    else:
        log(f"Failed to delete workspace {workspace_id}. Status: {response.status_code}")

# === Run Ansible ===
def run_playbook(ip):
    log(f"Running playbook on {ip}...")
    cmd = [
        "ansible-playbook",
        "-i", str(INVENTORY),
        str(PLAYBOOK),
        "-u", ssh_user,
        "--private-key", str(SSH_KEY),
        "-e", f"github_user={github_user}",
        "-e", f"github_token={github_token}",
        "-e", f"surf_api_key={surf_api_key}",
        "-e", "ansible_ssh_common_args='-o StrictHostKeyChecking=no'"
    ]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        log("Ansible playbook completed successfully.")
        log("Waiting 60 seconds before deleting workspace...")
        time.sleep(60)
        delete_workspace_by_id()
    else:
        log("❌ Ansible playbook failed. Workspace will NOT be deleted.")
    return result.returncode == 0

# === Main ===
def main():
    ensure_ssh_key()
    log("Checking for GitHub commit once...")
    latest = get_latest_commit()
    if not latest:
        log("Could not fetch latest commit.")
        return
    last = read_last_commit()
    if latest != last:
        log(f"New commit detected: {latest}")
        write_last_commit(latest)
        if create_workspace():
            if run_idfinder():
                ip = get_last_ip()
                if ip:
                    run_playbook(ip)
                else:
                    log("No IP found.")
    else:
        log("No new commits.")

if __name__ == "__main__":
    main()
