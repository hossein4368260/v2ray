import json
import os
import sys
import qrcode
import base64
import uuid
import subprocess

CLIENTS_FILE = '/usr/local/etc/v2ray/clients.json'
CONFIG_FILE = '/usr/local/etc/v2ray/config.json'

SERVER_ADDRESS = "نام دامنه رو اينجا بنويسيد"
SERVER_PORT = "443"
WS_PATH = "/ray"
TLS = "tls" # اگر TLS نيست خالي بگذار

def load_clients():
if not os.path.exists(CLIENTS_FILE):
return []
with open(CLIENTS_FILE, 'r', encoding='utf-8') as f:
return json.load(f)

def save_clients(clients):
with open(CLIENTS_FILE, 'w', encoding='utf-8') as f:
json.dump(clients, f, ensure_ascii=False, indent=2)

def load_config():
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
return json.load(f)

def save_config(config):
with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
json.dump(config, f, ensure_ascii=False, indent=2)

def update_config_clients(clients):
config = load_config()

# فرض بر اين است كه clients در config در مسير زير است:
# config["inbounds"][0]["settings"]["clients"]
try:
config_clients = config["inbounds"][0]["settings"]["clients"]
except KeyError:
print("فرمت فايل config.json غيرمنتظره است!")
return False

# تبديل clients به فرمتي كه config مي‌خواهد
new_config_clients = []
for c in clients:
new_config_clients.append({
"id": c['uuid'],
"alterId": 0,
"email": c['name']
})

config["inbounds"][0]["settings"]["clients"] = new_config_clients
save_config(config)
return True

def restart_v2ray_service():
print("در حال ريستارت سرويس v2ray ...")
try:
subprocess.run(['systemctl', 'restart', 'v2ray'], check=True)
print("سرويس v2ray با موفقيت ريستارت شد.")
except subprocess.CalledProcessError:
print("خطا در ريستارت سرويس v2ray! لطفا به صورت دستي بررسي كنيد.")

def list_clients(clients):
if not clients:
print("حسابي وجود ندارد.")
return
for i, c in enumerate(clients):
print(f"{i+1}. نام: {c['name']} - UUID: {c['uuid']}")

def add_client(name):
clients = load_clients()
if any(c['name'] == name for c in clients):
print("اين نام قبلا وجود دارد.")
return

new_uuid = str(uuid.uuid4())
clients.append({"name": name, "uuid": new_uuid})
save_clients(clients)

if update_config_clients(clients):
restart_v2ray_service()

print(f"حساب اضافه شد:\nنام: {name}\nUUID: {new_uuid}")

def remove_client(name_to_remove):
clients = load_clients()
new_clients = [c for c in clients if c['name'] != name_to_remove]

if len(new_clients) == len(clients):
print("اين حساب وجود ندارد.")
return

save_clients(new_clients)

if update_config_clients(new_clients):
restart_v2ray_service()

print("حساب حذف شد.")

def generate_qr(name_to_generate):
clients = load_clients()
client = next((c for c in clients if c['name'] == name_to_generate), None)
if client is None:
print("حساب پيدا نشد.")
return

vmess_json = {
"v": "2",
"ps": client['name'],
"add": SERVER_ADDRESS,
"port": SERVER_PORT,
"id": client['uuid'],
"aid": "0",
"net": "ws",
"type": "none",
"host": "",
"path": WS_PATH,
"tls": TLS
}
vmess_str = json.dumps(vmess_json, separators=(',', ':'))
vmess_b64 = base64.b64encode(vmess_str.encode()).decode()
vmess_link = f"vmess://{vmess_b64}"
print(f"لينك vmess براي {client['name']}:\n{vmess_link}\n")

qr = qrcode.QRCode()
qr.add_data(vmess_link)
qr.make(fit=True)
qr.print_ascii(invert=True)

def print_help():
print("""
Usage:
python3 v2ray.py add اضافه كردن حساب جديد (UUID خودكار ساخته مي‌شود)
python3 v2ray.py remove حذف حساب با نام
python3 v2ray.py list نمايش همه حساب‌ها
python3 v2ray.py qr ساخت و نمايش QR كد حساب با نام در ترمينال
""")

def main():
if len(sys.argv) < 2:
print_help()
return

cmd = sys.argv[1].lower()

if cmd == 'add' and len(sys.argv) == 3:
add_client(sys.argv[2])
elif cmd == 'remove' and len(sys.argv) == 3:
remove_client(sys.argv[2])
elif cmd == 'list':
clients = load_clients()
list_clients(clients)
elif cmd == 'qr' and len(sys.argv) == 3:
generate_qr(sys.argv[2])
else:
print_help()

if __name__ == '__main__':
main()