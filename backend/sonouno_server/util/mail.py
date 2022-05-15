"""Mail server config and management.
"""

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

from ..config import CONFIG

mail_conf = ConnectionConfig(
    MAIL_USERNAME=CONFIG.mail_username,
    MAIL_PASSWORD=CONFIG.mail_password,
    MAIL_FROM=CONFIG.mail_sender,
    MAIL_PORT=CONFIG.mail_port,
    MAIL_SERVER=CONFIG.mail_server,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
)

mail = FastMail(mail_conf)


async def send_verification_email(email: str, token: str):
    """Sends user verification email."""
    # Change this later to public endpoint
    url = CONFIG.server_host + '/iam/verify/' + token
    if CONFIG.mail_console:
        print('POST to ' + url)
    else:
        message = MessageSchema(
            recipients=[email],
            subject='sonoUno Email Verification',
            body='Welcome to sonoUno! We just need to verify your email to begin: '
            + url,
        )
        await mail.send_message(message)


async def send_password_reset_email(email: str, token: str):
    """Sends password reset email."""
    # Change this later to public endpoint
    url = CONFIG.server_host + '/iam/reset-password/' + token
    if CONFIG.mail_console:
        print('POST to ' + url)
    else:
        message = MessageSchema(
            recipients=[email],
            subject='sonoUno Password Reset',
            body=f'Click the link to reset your sonoUno account password: {url}\n'
            'If you did not request this, please ignore this email',
        )
        await mail.send_message(message)
