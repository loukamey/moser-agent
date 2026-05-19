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

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
EMAIL_SENDER = "meylanlouka@gmail.com"
EMAIL_PASSWORD = "aocs irmm zicx coel"
EMAIL_RECEIVER = "meylanlouka@gmail.com"

def scrape_moser_watches():
    listings = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        url = "https://www.chrono24.com/search/index.htm?query=h+moser+cie&dosearch=true"
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
        print(f"Scraper error: {e}")
    return listings

def generate_report(listings):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are a professional watch market analyst specializing in H. Moser & Cie.
Today's date: {datetime.now().strftime("%B %d, %Y")}

Listings found today: {json.dumps(listings, indent=2)}

Write a sharp professional daily briefing for a serious H. Moser & Cie collector covering:
- Current market activity
- Notable references (Endeavour, Pioneer, Streamliner, Funky Blue, Perpetual Calendar)
- Current price ranges in secondary market
- One market insight or recommendation

If no listings were found, write a general H. Moser & Cie market intelligence briefing based on current collector trends. Make it genuinely useful."""

    message = client.messages.create(
        model="claude-opus-4-5",
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
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Email error: {e}")

def daily_job():
    print(f"Running daily scan - {datetime.now()}")
    listings = scrape_moser_watches()
    print(f"Found {len(listings)} listings")
    print("Generating report...")
    report = generate_report(listings)
    send_email(f"Moser Daily Alert - {datetime.now().strftime('%B %d, %Y')}", report)

print("H. Moser & Cie Watch Agent is running!")
print(f"Started at: {datetime.now()}")
print("Sending test report now...")
daily_job()

schedule.every().day.at("04:00").do(daily_job)

while True:
    schedule.run_pending()
    time.sleep(60)
