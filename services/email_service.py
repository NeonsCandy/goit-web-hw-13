from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from config import settings
from auth import create_access_token

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_email(email: EmailStr, username: str, host: str):
    """
    Функція генерує токен для підтвердження та відправляє лист з посиланням.
    """
    try:
        token_verification = create_access_token(data={"sub": email})
        
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            body=f"""
            <p>Welcome, {username}!</p>
            <p>Please confirm your email by clicking the link below:</p>
            <p><a href="{host}auth/confirmed_email/{token_verification}">Confirm Email</a></p>
            """,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as err:
        print(f"Помилка відправки листа: {err}")