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

# Confirmed exact endpoint from DevTools
TICKET_API = "https://rcbscaleapi.ticketgenie.in/ticket/eventlist/0"

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
    try:
        r = requests.get(TICKET_API, headers=HEADERS, timeout=10)
        logging.info(f"ticket/eventlist/0 â†’ {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            result = data.get("result", {})

            # Currently result is {} (empty object) when no tickets
            # Tickets are live when result is a non-empty list or object
            is_empty = (result == {} or result == [] or result is None)

            if not is_empty:
                logging.info(f"Tickets found! Result: {result}")
                return True, (
                    "ðŸš¨ <b>RCB TICKETS ARE LIVE!</b>\n\n"
                    "âœ… API returned ticket data!\n\n"
                    "ðŸ‘‰ Buy now: https://shop.royalchallengers.com/ticket"
                )
            else:
                logging.info(f"No tickets yet. Result is empty: {result}")
        else:
            logging.warning(f"Unexpected status: {r.status_code}")

    except Exception as e:
        logging.warning(f"Error checking ticket API: {e}")

    return False, None

def validate_telegram():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            bot_name = r.json()["result"]["username"]
            logging.info(f"Telegram bot connected: @{bot_name}")
            return True
        else:
            logging.error(f"Invalid Telegram token! Response: {r.text}")
            return False
    except Exception as e:
        logging.error(f"Telegram validation failed: {e}")
        return False

def main():
    logging.info("RCB Ticket Monitor started ðŸ")
    logging.info(f"Monitoring: {TICKET_API}")
    logging.info(f"Checking every {CHECK_INTERVAL} seconds...")

    if not TELEGRAM_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_TOKEN or TELEGRAM_CHAT_ID env variable is missing! Exiting.")
        return

    if not validate_telegram():
        logging.error("Fix your TELEGRAM_TOKEN in Railway variables and redeploy.")
        return

    send_telegram(
        "âœ… <b>RCB Ticket Monitor is running!</b>\n\n"
        "ðŸŽ¯ Monitoring: <code>ticket/eventlist/0</code>\n"
        "â± Checking every 1 minute\n\n"
        "I'll notify you the moment tickets go live! ðŸ"
    )

    alert_sent = False

    while True:
        try:
            is_live, message = check_tickets()
            if is_live and not alert_sent:
                logging.info("TICKETS ARE LIVE! Sending alert...")
                # Send 3 times so you definitely don't miss it
                send_telegram(message)
                time.sleep(5)
                send_telegram(message)
                time.sleep(5)
                send_telegram(message)
                alert_sent = True
            elif not is_live:
                alert_sent = False
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
