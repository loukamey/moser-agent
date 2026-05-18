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
        url = "https://www.chrono24.com/search/index.htm?query=h+moser+cie"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.select(".article-item-container")[:15]:
            title = item.select_one(".article-title")
            price = item.select_one(".price")
            if title and price:
                listings.append({
                    "source": "Chrono24",
                    "type": "Secondary Market",
                    "title": title.text.strip(),
                    "price": price.text.strip(),
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"Chrono24 error: {e}")
    return listings

def scrape_auction_results():
    results = []
    try:
        url = "https://www.phillips.com/search#tabs=lots&q=moser"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.select(".lot-tile")[:10]:
            title = item.select_one(".lot-title")
            price = item.select_one(".lot-price")
            if title:
                results.append({
                    "source": "Phillips",
                    "type": "Auction",
                    "title": title.text.strip(),
                    "price": price.text.strip() if price else "TBD",
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"Phillips error: {e}")
    return results

def save_to_monthly_log(data):
    log_file = "monthly_log.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            existing = json.load(f)
    else:
        existing = []
    existing.extend(data)
    with open(log_file, "w") as f:
        json.dump(existing, f)

def load_monthly_log():
    log_file = "monthly_log.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return json.load(f)
    return []

def clear_monthly_log():
    with open("monthly_log.json", "w") as f:
        json.dump([], f)

def daily_analysis(listings, auctions):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are a professional watch market analyst specializing in H. Moser & Cie.
Today: {datetime.now().strftime("%B %d, %Y")}
LISTINGS: {json.dumps(listings, indent=2)}
AUCTIONS: {json.dumps(auctions, indent=2)}
Write a short sharp daily briefing covering new pieces, auction results, unusual pricing, and one market observation."""
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def monthly_analysis(all_data):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are a professional watch market analyst specializing in H. Moser & Cie.
Month: {datetime.now().strftime("%B %Y")}
DATA: {json.dumps(all_data, indent=2)}
Write a comprehensive monthly report with executive summary, price trends, auction results, rarity signals, statistics, and market outlook."""
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
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
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Email error: {e}")

def daily_job():
    print(f"Running daily scan - {datetime.now()}")
    listings = scrape_moser_watches()
    auctions = scrape_auction_results()
    all_found = listings + auctions
    if all_found:
        save_to_monthly_log(all_found)
        analysis = daily_analysis(listings, auctions)
        send_email(f"Moser Daily Alert - {datetime.now().strftime('%B %d, %Y')}", analysis)
    else:
        print("No new listings found today")

def monthly_job():
    print(f"Running monthly analysis - {datetime.now()}")
    all_data = load_monthly_log()
    if all_data:
        analysis = monthly_analysis(all_data)
        send_email(f"Moser Monthly Report - {datetime.now().strftime('%B %Y')}", analysis)
        clear_monthly_log()

schedule.every().day.at("04:00").do(daily_job)
schedule.every().monday.at("04:00").do(lambda: datetime.now().day <= 7 and monthly_job())

print("H. Moser & Cie Watch Agent is running!")
print("Daily alerts: every day at 8:00am Dubai time")
print("Monthly report: first Monday of each month")
print(f"Started at: {datetime.now()}")

while True:
    schedule.run_pending()
    time.sleep(60)
