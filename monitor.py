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
CHECK_INTERVAL = 30  # seconds

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://shop.royalchallengers.com",
    "Referer": "https://shop.royalchallengers.com/",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/124.0 Mobile Safari/537.36"
}

# Confirmed exact endpoint from DevTools
TICKET_API = "https://rcbscaleapi.ticketgenie.in/ticket/eventlist/0"

# Alert only when this team appears in team_1 or team_2
TARGET_TEAM = "Chennai Super Kings"

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
        logging.info(f"ticket/eventlist/0 → {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            result = data.get("result", {})

            # result is a list when events are available
            if not isinstance(result, list) or len(result) == 0:
                logging.info("No events in result yet.")
                return False, None

            # Log all available matches
            logging.info(f"Found {len(result)} event(s):")
            for event in result:
                t1 = event.get("team_1", "")
                t2 = event.get("team_2", "")
                name = event.get("event_Name", "")
                date = event.get("event_Display_Date", "")
                logging.info(f"  → {name} | {date}")

                # Check if CSK is playing
                if TARGET_TEAM.lower() in t1.lower() or TARGET_TEAM.lower() in t2.lower():
                    price = event.get("event_Price_Range", "N/A")
                    venue = event.get("venue_Name", "N/A")
                    city = event.get("city_Name", "N/A")
                    return True, (
                        f"🚨 <b>RCB vs CSK TICKETS ARE LIVE!</b> 🔴💛\n\n"
                        f"🏏 <b>{name}</b>\n"
                        f"📅 {date}\n"
                        f"🏟 {venue}, {city}\n"
                        f"💰 {price}\n\n"
                        f"👉 <a href='https://shop.royalchallengers.com/ticket'>BUY TICKETS NOW</a>"
                    )

            logging.info(f"CSK match not found yet in {len(result)} event(s).")

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
    logging.info("RCB Ticket Monitor started 🏏")
    logging.info(f"Monitoring: {TICKET_API}")
    logging.info(f"Alerting for: {TARGET_TEAM}")
    logging.info(f"Checking every {CHECK_INTERVAL} seconds...")

    if not TELEGRAM_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_TOKEN or TELEGRAM_CHAT_ID env variable is missing! Exiting.")
        return

    if not validate_telegram():
        logging.error("Fix your TELEGRAM_TOKEN in Railway variables and redeploy.")
        return

    send_telegram(
        "✅ <b>RCB Ticket Monitor is running!</b>\n\n"
        f"🎯 Watching for: <b>{TARGET_TEAM}</b> match tickets\n"
        "⏱ Checking every 30 seconds\n\n"
        "I'll notify you the moment CSK tickets go live! 🏏"
    )

    alert_sent = False

    while True:
        try:
            is_live, message = check_tickets()
            if is_live and not alert_sent:
                logging.info("CSK MATCH TICKETS ARE LIVE! Sending alert...")
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
