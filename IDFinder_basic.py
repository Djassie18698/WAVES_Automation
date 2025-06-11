from pathlib import Path
import requests, json, time, os
from datetime import datetime, timezone

ROOT = Path(__file__).parent.resolve()
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

API_URL = "https://gw.live.surfresearchcloud.nl/v1/workspace/workspaces/"
API_KEY = "5489d9fc169ae40148a2cfbf1644a130f891e37f964d34e60f22fb50c5272289"

NAME_LOG_FILE = DATA_DIR / "last_workspace_names.txt"
OUTPUT_LOG_FILE = DATA_DIR / "workspace_ip_lookup.json"
INVENTORY_FILE = ROOT / "inventory.ini"
INVENTORY_GROUP = "myhosts"

HEADERS = {
    "accept": "application/json;Compute",
    "authorization": f"{API_KEY}"
}

def get_last_workspace_name():
    try:
        with open(NAME_LOG_FILE, "r") as f:
            return f.readline().strip()
    except:
        print("Failed to read workspace name.")
        return None

def find_workspace_info(name):
    try:
        params = {"application_type": "Compute", "deleted": "false"}
        r = requests.get(API_URL, headers=HEADERS, params=params)
        r.raise_for_status()
        for ws in r.json().get("results", []):
            if ws.get("name") == name:
                return {
                    "id": ws["id"],
                    "status": ws["status"],
                    "created": ws["time_created"],
                    "fqdn": ws["meta"].get("workspace_fqdn", ""),
                    "name": ws["name"]
                }
        return None
    except:
        print("Error finding workspace.")
        return None

def get_ip_by_id(workspace_id, max_retries=30, delay=20):
    for i in range(max_retries):
        try:
            r = requests.get(f"{API_URL}{workspace_id}/", headers=HEADERS)
            r.raise_for_status()
            ip = r.json().get("resource_meta", {}).get("ip", "")
            if ip:
                return ip
            print(f"Waiting for IP... ({i+1})")
            time.sleep(delay)
        except:
            print("Failed to fetch IP. Retrying...")
            time.sleep(delay)
    return ""

def append_ip_to_inventory(ip):
    ssh_user = os.environ.get("ANSIBLE_SSH_USER", "dean")
    line = f"{ip} ansible_user={ssh_user} ansible_ssh_private_key_file=~/.ssh/surfspotkey"

    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "r") as f:
            if line in f.read():
                print(f"Entry already in inventory: {line}")
                return

    with open(INVENTORY_FILE, "a" if os.path.exists(INVENTORY_FILE) else "w") as f:
        if os.path.getsize(INVENTORY_FILE) == 0:
            f.write(f"[{INVENTORY_GROUP}]\n")
        f.write(f"{line}\n")

    print(f"📋 Inventory updated: {line}")


def save_result(data):
    with open(OUTPUT_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    name = get_last_workspace_name()
    if not name:
        print("No workspace name.")
        exit()
    info = find_workspace_info(name)
    if not info:
        print("Workspace not found.")
        exit()
    ip = get_ip_by_id(info["id"])
    if not ip:
        print("No IP found.")
        exit()
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name": info["name"],
        "workspace_id": info["id"],
        "status": info["status"],
        "created": info["created"],
        "fqdn": info["fqdn"],
        "ip": ip
    }
    save_result(data)
    append_ip_to_inventory(ip)
    print("Done.")
