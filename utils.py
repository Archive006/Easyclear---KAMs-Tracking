import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

def send_email_reminder(company_name, last_contact_date, days_since):
    sender = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASS')
    recipients = ["samuel@easyclear.co.za", "leon@easyclear.co.za"]

    subject = f"Courtesy Call Reminder: {company_name}"
    html = f"""
    <html><body style='font-family:Segoe UI, sans-serif;'>
    <div style='background-color:#001F54; color:#fff; padding:10px;'>
        <h2>Courtesy Call Reminder</h2>
    </div>
    <p><b>Company:</b> {company_name}</p>
    <p><b>Last Contact:</b> {last_contact_date}</p>
    <p><b>Days Since:</b> {days_since}</p>
    <p>Please follow up as soon as possible.</p>
    </body></html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent for {company_name}")
    except Exception as e:
        print(f"Email failed for {company_name}: {e}")
