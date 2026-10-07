import smtplib
import ssl
from email.mime.text import MIMEText

smtp_user = "hansidantuluri@gmail.com"
smtp_password = "mpzdsxnzcyetlday"  # paste your 16-char app password

msg = MIMEText("Test email from AVIDSTOCKS")
msg['Subject'] = "Test"
msg['From'] = smtp_user
msg['To'] = smtp_user  # sending to yourself

context = ssl.create_default_context()

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, smtp_user, msg.as_string())
        print("Email sent successfully!")
except Exception as e:
    print(f"Failed: {type(e).__name__}: {e}")