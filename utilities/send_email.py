import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(name: str, surname: str, email: str, added_info: str = None):
    smtp_server = "smtp-mail.outlook.com"  # SMTP-сервер
    smtp_port = 587  # порт SMTP-сервера
    smtp_user = "DM_Kondrasov@vcot.info"
    smtp_password = open('email_password.txt', 'r').read()

    sender_email = "DM_Kondrasov@vcot.info"
    receiver_email = "dm_kondrasov@vnii-truda.ru"
    subject = "skill-calculator: ЗАПРОС НА ВОССТАНОВЛЕНИЕ ПАРОЛЯ."
    body = f"Запрос на восстановление от {surname} {name} на почту {email}.\nДополнительная информация:\n" \
           f"{added_info if added_info else 'отсутствует'}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(smtp_server, smtp_port)
    try:
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
    except Exception:
        pass
    finally:
        server.quit()


def send_email_assync(name: str, surname: str, email: str, added_info: str = None):
    thread = threading.Thread(target=send_email, args=(name, surname, email, added_info))
    thread.start()
