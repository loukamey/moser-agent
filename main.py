import requests
from bs4 import BeautifulSoup
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
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        url = "https://www.chrono24.com/search/index.htm?query=h+moser+cie&dosearch=true"
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all("div", class_=lambda x: x and "article" in x.lower())[:10]:
            title = item.find(["h3", "h2", "a"])
            price = item.find(string=lambda x: x and ("CHF" in x or "USD" in x or "EUR" in x or "AED" in x))
            if title and title.text.strip():
                listings.append({
                    "source": "Chrono24",
                    "title": title.text.strip()[:100],
                    "price": price.strip() if price else "Price on request",
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"Scraper error: {e}")
    return listings

def check_urgent(listings):
    if not listings:
        return False, ""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are an H. Moser & Cie expert.
Listings: {json.dumps(listings, indent=2)}

Is there something TRULY URGENT? Only flag if: extremely rare reference (Concept, Funky Blue Perpetual, Tourbillon), record auction price, or piece priced 20%+ below market value.

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
Listings: {json.dumps(listings, indent=2)}

Write a sharp professional daily briefing covering market activity, notable references, prices and one insight. Keep under 4000 characters."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def hourly_check():
    print(f"Hourly urgent check - {datetime.now()}")
    listings = scrape_moser_watches()
    is_urgent, reason = check_urgent(listings)
    if is_urgent:
        alert = f"🚨‼️\n\n<b>LOUKA — ACT NOW</b>\n\n{reason}\n\n→ chrono24.com/search/?query=h+moser+cie\n→ phillips.com\n\n⏰ {datetime.now().strftime('%H:%M')} Dubai time"
        send_telegram(alert)
        print(f"URGENT ALERT SENT: {reason}")

def daily_job():
    print(f"Running daily scan - {datetime.now()}")
    listings = scrape_moser_watches()
    report = generate_report(listings)
    message = f"⌚ <b>Moser Daily Alert - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}"
    send_telegram(message)

print("H. Moser & Cie Watch Agent is running!")
print(f"Started at: {datetime.now()}")
daily_job()

schedule.every().day.at("04:00").do(daily_job)
schedule.every(1).hours.do(hourly_check)

while True:
    schedule.run_pending()
    time.sleep(60)
