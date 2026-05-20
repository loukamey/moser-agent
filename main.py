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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

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

def scrape_all():
    listings = []

    # Chrono24
    try:
        url = "https://www.chrono24.com/search/index.htm?query=h+moser+cie&dosearch=true&watchTypes=U"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.find_all(["article", "div"], class_=lambda x: x and any(c in str(x) for c in ["article", "listing"]))[:15]:
            title = item.find(["h3", "h2", "a"])
            price = item.find(string=lambda x: x and any(c in str(x) for c in ["CHF", "USD", "EUR", "$", "€"]))
            if title and title.text.strip() and len(title.text.strip()) > 5:
                listings.append({"source": "Chrono24", "title": title.text.strip()[:100], "price": price.strip() if price else "POA"})
    except Exception as e:
        print(f"Chrono24 error: {e}")

    # Phillips
    try:
        url = "https://www.phillips.com/search#tabs=lots&q=moser"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.find_all(["div", "article"], class_=lambda x: x and "lot" in str(x).lower())[:10]:
            title = item.find(["h2", "h3", "h4", "a"])
            price = item.find(string=lambda x: x and any(c in str(x) for c in ["CHF", "USD", "EUR", "$", "€"]))
            if title and title.text.strip() and len(title.text.strip()) > 5:
                listings.append({"source": "Phillips Auction", "title": title.text.strip()[:100], "price": price.strip() if price else "See auction", "type": "AUCTION"})
    except Exception as e:
        print(f"Phillips error: {e}")

    # Sothebys
    try:
        url = "https://www.sothebys.com/en/buy/watches?query=moser"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.find_all(["div", "article"], class_=lambda x: x and any(c in str(x) for c in ["lot", "card"]))[:10]:
            title = item.find(["h2", "h3", "h4", "a"])
            if title and title.text.strip() and len(title.text.strip()) > 5:
                listings.append({"source": "Sothebys", "title": title.text.strip()[:100], "price": "See auction", "type": "AUCTION"})
    except Exception as e:
        print(f"Sothebys error: {e}")

    # Christies
    try:
        url = "https://www.christies.com/en/results?keyword=moser+watch"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.find_all(["div", "article"], class_=lambda x: x and any(c in str(x) for c in ["lot", "card", "result"]))[:10]:
            title = item.find(["h2", "h3", "h4", "a"])
            if title and title.text.strip() and len(title.text.strip()) > 5:
                listings.append({"source": "Christies", "title": title.text.strip()[:100], "price": "See auction", "type": "AUCTION"})
    except Exception as e:
        print(f"Christies error: {e}")

    print(f"Total listings found: {len(listings)}")
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
    message = client.messages.create(model="claude-opus-4-5", max_tokens=100, messages=[{"role": "user", "content": prompt}])
    reply = message.content[0].text.strip()
    if reply.startswith("URGENT:"):
        return True, reply.replace("URGENT:", "").strip()
    return False, ""

def generate_report(listings):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are a professional watch market analyst specializing in H. Moser & Cie.
Today: {datetime.now().strftime("%B %d, %Y")}
Sources checked: Chrono24, Phillips, Sotheby's, Christie's
Listings found: {json.dumps(listings, indent=2)}
Write a sharp professional daily briefing covering all listings, prices, auction results, notable references, and one market insight. Keep under 4000 characters. If no listings found, write general Moser market intelligence."""
    message = client.messages.create(model="claude-opus-4-5", max_tokens=1000, messages=[{"role": "user", "content": prompt}])
    return message.content[0].text

def hourly_check():
    print(f"Hourly check - {datetime.now()}")
    listings = scrape_all()
    is_urgent, reason = check_urgent(listings)
    if is_urgent:
        alert = f"🚨‼️ LOUKA — ACT NOW\n\n{reason}\n\n→ chrono24.com/search/?query=h+moser+cie\n→ phillips.com\n\n⏰ {datetime.now().strftime('%H:%M')} Dubai time"
        send_telegram(alert)

def daily_job():
    print(f"Daily scan - {datetime.now()}")
    listings = scrape_all()
    report = generate_report(listings)
    send_telegram(f"⌚ <b>Moser Daily Alert - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}")

print("H. Moser & Cie Watch Agent running!")
print(f"Started: {datetime.now()}")
daily_job()

schedule.every().day.at("04:00").do(daily_job)
schedule.every(1).hours.do(hourly_check)

while True:
    schedule.run_pending()
    time.sleep(60)
