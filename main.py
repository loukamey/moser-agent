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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
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

def scrape_chrono24():
    listings = []
    try:
        urls = [
            "https://www.chrono24.com/search/index.htm?query=h+moser+cie&dosearch=true&watchTypes=U",
            "https://www.chrono24.com/search/index.htm?manufacturerIds=3624&dosearch=true",
        ]
        for url in urls:
            response = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.find_all(["article", "div"], class_=lambda x: x and any(c in str(x) for c in ["article", "listing", "watch"]))[:15]:
                title = item.find(["h3", "h2", "h1", "a", "span"], class_=lambda x: x and any(c in str(x) for c in ["title", "name", "model"]))
                price = item.find(string=lambda x: x and any(c in str(x) for c in ["CHF", "USD", "EUR", "AED", "$", "€"]))
                if title and title.text.strip() and len(title.text.strip()) > 5:
                    listings.append({
                        "source": "Chrono24",
                        "title": title.text.strip()[:100],
                        "price": price.strip() if price else "POA",
                        "url": url
                    })
    except Exception as e:
        print(f"Chrono24 error: {e}")
    return listings

def scrape_watchbox():
    listings = []
    try:
        url = "https://www.watchbox.com/search?q=moser"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all(["div", "article"], class_=lambda x: x and any(c in str(x) for c in ["product", "watch", "listing"]))[:10]:
            title = item.find(["h2", "h3", "a", "span"])
            price = item.find(string=lambda x: x and "$" in str(x))
            if title and title.text.strip() and "moser" in title.text.lower():
                listings.append({
                    "source": "WatchBox",
                    "title": title.text.strip()[:100],
                    "price": price.strip() if price else "POA",
                })
    except Exception as e:
        print(f"WatchBox error: {e}")
    return listings

def scrape_phillips():
    listings = []
    try:
        urls = [
            "https://www.phillips.com/search#tabs=lots&q=moser",
            "https://www.phillips.com/watches",
        ]
        for url in urls:
            response = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.find_all(["div", "article"], class_=lambda x: x and any(c in str(x) for c in ["lot", "item", "result"]))[:10]:
                title = item.find(["h2", "h3", "h4", "a"])
                price = item.find(string=lambda x: x and any(c in str(x) for c in ["CHF", "USD", "EUR", "$", "€"]))
                if title and title.text.strip() and len(title.text.strip()) > 5:
                    listings.append({
                        "source": "Phillips Auction",
                        "title": title.text.strip()[:100],
                        "price": price.strip() if price else "See auction",
                        "type": "AUCTION"
                    })
    except Exception as e:
        print(f"Phillips error: {e}")
    return listings

def scrape_sothebys():
    listings = []
    try:
        url = "https://www.sothebys.com/en/buy/watches?query=moser"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all(["div", "article"], class_=lambda x: x and any(c in str(x) for c in ["lot", "item", "card"]))[:10]:
            title = item.find(["h2", "h3", "h4", "a"])
            price = item.find(string=lambda x: x and any(c in str(x) for c in ["CHF", "USD", "EUR", "$", "€"]))
            if title and title.text.strip() and len(title.text.strip()) > 5:
                listings.append({
                    "source": "Sotheby's Auction",
                    "title": title.text.strip()[:100],
                    "price": price.strip() if price else "See auction",
                    "type": "AUCTION"
                })
    except Exception as e:
        print(f"Sothebys error: {e}")
    return listings

def scrape_christies():
    listings = []
    try:
        url = "https://www.christies.com/en/results?keyword=moser+watch"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all(["div", "article"], class_=lambda x: x and any(c in str(x) for c in ["lot", "item", "card", "result"]))[:10]:
            title = item.find(["h2", "h3", "h4", "a"])
            price = item.find(string=lambda x: x and any(c in str(x) for c in ["CHF", "USD", "EUR", "$", "€"]))
            if title and title.text.strip() and len(title.text.strip()) > 5:
                listings.append({
                    "source": "Christie's Auction",
                    "title": title.text.strip()[:100],
                    "price": price.strip() if price else "See auction",
                    "type": "AUCTION"
                })
    except Exception as e:
        print(f"Christies error: {e}")
    return listings

def scrape_antiquorum():
    listings = []
    try:
        url = "https://www.antiquorum.swiss/en/watches?q=moser"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all(["div", "article"])[:10]:
            title = item.find(["h2", "h3", "h4", "a"])
            price = item.find(string=lambda x: x and any(c in str(x) for c in ["CHF", "USD", "EUR", "$", "€"]))
            if title and title.text.strip() and "moser" in title.text.lower():
                listings.append({
                    "source": "Antiquorum Auction",
                    "title": title.text.strip()[:100],
                    "price": price.strip() if price else "See auction",
                    "type": "AUCTION"
                })
    except Exception as e:
        print(f"Antiquorum error: {e}")
    return listings

def scrape_all():
    print("Scraping all sources...")
    all_listings = []
    all_listings.extend(scrape_chrono24())
    print(f"Chrono24: {len(all_listings)}")
    all_listings.extend(scrape_watchbox())
    print(f"WatchBox: {len(all_listings)}")
    all_listings.extend(scrape_phillips())
    print(f"Phillips: {len(all_listings)}")
    all_listings.extend(scrape_sothebys())
    print(f"Sothebys: {len(all_listings)}")
    all_listings.extend(scrape_christies())
    print(f"Christies: {len(all_listings)}")
    all_listings.extend(scrape_antiquorum())
    print(f"Antiquorum: {len(all_listings)}")
    return all_listings

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
Sources checked: Chrono24, WatchBox, Phillips, Sotheby's, Christie's, Antiquorum
Listings found: {json.dumps(listings, indent=2)}

Write a sharp professional daily briefing covering:
- All secondary market listings found today with prices
- All auction results and upcoming lots
- Notable references spotted
- Price analysis
- Market insight
Keep under 4000 characters. If no listings found, write general Moser market intelligence."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def hourly_check():
    print(f"Hourly urgent check - {datetime.now()}")
    listings = scrape_all()
    is_urgent, reason = check_urgent(listings)
    if is_urgent:
        alert = f"🚨‼️ LOUKA — ACT NOW\n\n{reason}\n\n→ chrono24.com/search/?query=h+moser+cie\n→ phillips.com\n\n⏰ {datetime.now().strftime('%H:%M')} Dubai time"
        send_telegram(alert)
        print(f"URGENT ALERT SENT: {reason}")

def daily_job():
    print(f"Running daily scan - {datetime.now()}")
    listings = scrape_all()
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
