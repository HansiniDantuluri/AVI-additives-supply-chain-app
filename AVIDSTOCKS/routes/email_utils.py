import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def is_valid_email(email):
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None


def send_order_email(mail, supplier_email, supplier_name, items):
    supplier_email = (supplier_email or '').strip()
    if not is_valid_email(supplier_email):
        raise ValueError(f"Invalid supplier email address: {supplier_email!r}")

    subject = 'New Purchase Order from AVIDSTOCKS'
    supplier_name = (supplier_name or 'Supplier').strip() or 'Supplier'

    body_lines = [
        f'Dear {supplier_name},',
        '',
        'Please find below the requested purchase order items:',
        '',
    ]

    if not items:
        body_lines.append('No items were provided.')
    else:
        for item in items:
            material_name = item.get('material_name', 'Unnamed material')
            quantity = item.get('quantity', '')
            body_lines.append(f'- {material_name}: {quantity}')

    body_lines.extend(['', 'Thank you,', 'AVIDSTOCKS'])
    body = '\n'.join(body_lines)

    smtp_user = "hansidantuluri@gmail.com"
    smtp_password = "mpzdsxnzcyetlday"

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = supplier_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, supplier_email, msg.as_string())