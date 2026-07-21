from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
)

from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)


async def send_welcome_email(
    email: str,
):
    message = MessageSchema(
        subject="Welcome!",
        recipients=[email],
        body="""
        Welcome to Employee Management API.

        Your account has been created successfully.
        """,
        subtype="plain",
    )

    fm = FastMail(conf)

    await fm.send_message(message)
