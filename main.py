import requests
from bs4 import BeautifulSoup
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import os
import anthropic

ANTHROPIC_API_KEY = "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"
EMAIL_SENDER = "loukamey@icloud.com"
EMAIL_PASSWORD = "iqku-ityt-kwds-ikmc"
EMAIL_RECEIVER = "loukamey@icloud.com"

def scrape_moser_watches():
    listings = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        url = "https://www.chrono24.com/search/index.htm?query=h+moser+cie&dosearch=true&searchexplain=1"
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all("div", class_=lambda x: x and "article" in x.lower())[:10]:
            title = item.find(["h3", "h2", "a"])
            price = item.find(string=lambda x: x and ("CHF" in x or "USD" in x or "EUR" in x or "AED" in x))
            if title and title.text.strip():
                listings.append({
                    "source": "Chrono24",
                    "type": "Secondary Market",
                    "title": title.text.strip()[:100],
                    "price": price.strip() if price else "Price on request",
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"Chrono24 error: {e}")

    try:
        url = "https://www.watchuseek.com/search/posts?keywords=moser&forums[0]=8"
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all("div", class_="structItem")[:5]:
            title = item.find("a", class_="structItem-title")
            if title:
                listings.append({
                    "source": "WatchUSeek Forum",
                    "type": "Community Listing",
                    "title": title.text.strip()[:100],
                    "price": "See listing",
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"WatchUSeek error: {e}")

    return listings

def scrape_auction_results():
    results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        url = "https://www.phillips.com/search#tabs=lots&q=h+moser"
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all(["div", "article"], class_=lambda x: x and "lot" in x.lower())[:5]:
            title = item.find(["h3", "h2", "a"])
            if title and title.text.strip():
                results.append({
                    "source": "Phillips Auction",
                    "type": "Auction",
                    "title": title.text.strip()[:100],
                    "price": "See auction",
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"Phillips error: {e}")
    return results

def generate_report(listings, auctions):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    if not listings and not auctions:
        market_note = "No new listings were scraped today from secondary market sources."
    else:
        market_note = f"Found {len(listings)} secondary market listings and {len(auctions)} auction results."

    prompt = f"""You are a professional watch market analyst specializing in H. Moser & Cie.
Today's date: {datetime.now().strftime("%B %d, %Y")}

Market scan results: {market_note}

Secondary market data: {json.dumps(listings, indent=2)}
Auction data: {json.dumps(auctions, indent=2)}

Write a sharp professional daily briefing for a serious H. Moser & Cie collector covering:
- Current market activity for H. Moser & Cie
- Notable references to watch (Endeavour, Pioneer, Streamliner, Funky Blue, Perpetual Calendar)
- Current price ranges for key references in secondary market
- Any auction highlights
- One market insight or recommendation for today

If no listings were found today, write a general H. Moser & Cie market intelligence briefing based on your knowledge of the brand, current collector trends, and what to look for in the secondary market. Make it genuinely useful."""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP("smtp.mail.me.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email sent successfully: {subject}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def daily_job():
    print(f"Running daily scan - {datetime.now()}")
    listings = scrape_moser_watches()
    auctions = scrape_auction_results()
    print(f"Found {len(listings)} listings and {len(auctions)} auctions")
    report = generate_report(listings, auctions)
    send_email(f"Moser Daily Alert - {datetime.now().strftime('%B %d, %Y')}", report)

def monthly_job():
    print(f"Running monthly analysis - {datetime.now()}")
    all_data = []
    if os.path.exists("monthly_log.json"):
        with open("monthly_log.json", "r") as f:
            all_data = json.load(f)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Write a comprehensive monthly H. Moser & Cie market report for {datetime.now().strftime("%B %Y")} covering market trends, price analysis, auction results, rarity signals, and investment outlook."""
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )
    send_email(f"Moser Monthly Report - {datetime.now().strftime('%B %Y')}", message.content[0].text)

print("H. Moser & Cie Watch Agent is running!")
print(f"Started at: {datetime.now()}")
print("Sending test report now...")
daily_job()

schedule.every().day.at("04:00").do(daily_job)
schedule.every().monday.at("04:00").do(lambda: datetime.now().day <= 7 and monthly_job())

while True:
    schedule.run_pending()
    time.sleep(60)
