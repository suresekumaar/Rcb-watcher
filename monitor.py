import requests
import time
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 60  # seconds

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://shop.royalchallengers.com",
    "Referer": "https://shop.royalchallengers.com/",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/124.0 Mobile Safari/537.36"
}

ENDPOINTS_TO_TRY = [
    "https://rcbscaleapi.ticketgenie.in/ticket",
    "https://rcbscaleapi.ticketgenie.in/tickets",
    "https://rcbscaleapi.ticketgenie.in/event",
    "https://rcbscaleapi.ticketgenie.in/events",
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            logging.info("Telegram alert sent!")
        else:
            logging.error(f"Telegram error: {r.text}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

def check_tickets():
    # Check 1: Does /ticket API endpoint return results?
    for endpoint in ENDPOINTS_TO_TRY:
        try:
            r = requests.get(endpoint, headers=HEADERS, timeout=10)
            logging.info(f"{endpoint} → {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                # If result array is non-empty, tickets are live!
                result = data.get("result", [])
                status = data.get("status", "")
                if isinstance(result, list) and len(result) > 0:
                    return True, f"🚨 <b>RCB TICKETS ARE LIVE!</b>\n\n✅ Endpoint: {endpoint}\n🎟 Items found: {len(result)}\n\n👉 Buy now: https://shop.royalchallengers.com/ticket"
        except Exception as e:
            logging.warning(f"Error checking {endpoint}: {e}")

    # Check 2: Does the /ticket page stop redirecting to /merchandise?
    try:
        r = requests.get(
            "https://shop.royalchallengers.com/ticket",
            headers=HEADERS,
            timeout=10,
            allow_redirects=True
        )
        final_url = r.url
        logging.info(f"shop.royalchallengers.com/ticket → final URL: {final_url}")
        if "merchandise" not in final_url and r.status_code == 200:
            return True, f"🚨 <b>RCB TICKETS ARE LIVE!</b>\n\n✅ Ticket page is now accessible!\n\n👉 Buy now: https://shop.royalchallengers.com/ticket"
    except Exception as e:
        logging.warning(f"Error checking main URL: {e}")

    return False, None

def main():
    logging.info("RCB Ticket Monitor started 🏏")
    logging.info(f"Checking every {CHECK_INTERVAL} seconds...")
    send_telegram("✅ <b>RCB Ticket Monitor is running!</b>\n\nI'll notify you the moment tickets go live. Checking every 1 minute. 🏏")

    alert_sent = False

    while True:
        try:
            is_live, message = check_tickets()
            if is_live and not alert_sent:
                logging.info("TICKETS ARE LIVE! Sending alert...")
                send_telegram(message)
                # Send 3 times to make sure you don't miss it
                time.sleep(5)
                send_telegram(message)
                time.sleep(5)
                send_telegram(message)
                alert_sent = True
            elif not is_live:
                logging.info("No tickets yet. Checking again in 1 minute...")
                alert_sent = False  # Reset in case tickets go offline and come back
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
