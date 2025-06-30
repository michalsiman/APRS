import aprslib
import requests
import json
import os
from datetime import datetime, timezone



# Přihlašovací údaje
CALLSIGN = "OK1SIM" #prihlasovaci callsign
PASSCODE = "17591" #passcode pro prihlaseni
TARGET = "OK1SIM-15" #adresa na kterou prichazi zpravy

# Cesty k souborům
CACHE_FILE = "processed_messages.json"
LOG_FILE = "message_log.txt"

# Načtení cache z předchozího běhu
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        processed_messages = set(json.load(f))
else:
    processed_messages = set()

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(list(processed_messages), f)

def log_message(timestamp, sender, recipient, message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | From: {sender} | To: {recipient} | Text: {message}\n")

def handle_packet(packet):
    if packet.get('format') == 'message' and packet.get('addresse') == TARGET:
        sender = packet.get('from')
        msg_no = packet.get('msgNo')
        message = packet.get('message_text', '')
        msg_id = f"{sender}:{msg_no}"

        if msg_id in processed_messages:
            return

        processed_messages.add(msg_id)
        save_cache()

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"\n📩 Zpráva přijata v {timestamp}")
        print(f"Od: {sender}")
        print(f"Pro: {TARGET}")
        print(f"Text: {message}")
        print("-" * 40)

        log_message(timestamp, sender, TARGET, message)

        if message.startswith("CL "):
            command = message[3:].strip()
            url = f"http://okff.cz/prikaz?cmd={command}"
            try:
                response = requests.get(url)
                print(f"🌐 HTTP požadavek odeslán na: {url}")
                print(f"📥 Odpověď serveru: {response.status_code} {response.text}")
            except Exception as e:
                print(f"❌ Chyba při odesílání požadavku: {e}")

def main():
    ais = aprslib.IS(CALLSIGN, passwd=PASSCODE, host="rotate.aprs2.net", port=14580)
    ais.set_filter("t/m")
    ais.connect()
    print(f"🔍 Sledování zpráv typu 'message' pro {TARGET} zahájeno...")
    ais.consumer(callback=handle_packet, immortal=True)

if __name__ == "__main__":
    main()
