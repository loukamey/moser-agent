import chrono24
import requests
import schedule
import time
from datetime import datetime
import json
import os
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = "8903199481:AAGksSeAZ-iY2IJE607yu1r-tFDiOxSqRCA"
TELEGRAM_CHAT_ID = "8526660731"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("Telegram message sent!")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

def scrape_moser_watches():
    listings = []
    try:
        results = chrono24.query("H. Moser").standard_search()
        for watch in results[:20]:
            listings.append({
                "source": "Chrono24",
                "title": watch.get("title", ""),
                "price": watch.get("price", "POA"),
                "location": watch.get("location", ""),
                "url": watch.get("url", ""),
                "date": datetime.now().strftime("%Y-%m-%d")
            })
        print(f"Chrono24 library found {len(listings)} listings")
    except Exception as e:
        print(f"Chrono24 library error: {e}")
    return listings

def check_urgent(listings):
    if not listings:
        return False, ""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are an H. Moser & Cie expert.
Listings: {json.dumps(listings, indent=2)}

Is there something TRULY URGENT? Only flag if: extremely rare reference (Concept, Funky Blue Perpetual, Tourbillon, limited edition), record auction price, or piece priced 20%+ below market value.

Reply ONLY with:
URGENT: [one sentence: what it is, price, why urgent]
or
NOT URGENT"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    reply = message.content[0].text.strip()
    if reply.startswith("URGENT:"):
        return True, reply.replace("URGENT:", "").strip()
    return False, ""

def generate_report(listings):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are a professional watch market analyst specializing in H. Moser & Cie.
Today: {datetime.now().strftime("%B %d, %Y")}
Live listings found today: {json.dumps(listings, indent=2)}

Write a sharp professional daily briefing covering:
- All live secondary market listings with prices and locations
- Notable references spotted
- Price analysis and market trends
- One market insight
Keep under 4000 characters."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def hourly_check():
    print(f"Hourly urgent check - {datetime.now()}")
    listings = scrape_moser_watches()
    is_urgent, reason = check_urgent(listings)
    if is_urgent:
        alert = f"🚨‼️ LOUKA — ACT NOW\n\n{reason}\n\n→ chrono24.com/search/?query=h+moser+cie\n\n⏰ {datetime.now().strftime('%H:%M')} Dubai time"
        send_telegram(alert)
        print(f"URGENT ALERT SENT: {reason}")

def daily_job():
    print(f"Running daily scan - {datetime.now()}")
    listings = scrape_moser_watches()
    print(f"Total listings found: {len(listings)}")
    report = generate_report(listings)
    message = f"⌚ <b>Moser Daily Alert - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}"
    send_telegram(message)

print("H. Moser & Cie Watch Agent is running!")
print(f"Started: {datetime.now()}")
daily_job()

schedule.every().day.at("04:00").do(daily_job)
schedule.every(1).hours.do(hourly_check)

while True:
    schedule.run_pending()
    time.sleep(60)
