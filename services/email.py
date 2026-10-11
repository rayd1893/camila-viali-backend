"""Envio de correo via SMTP, usado por el flujo de recuperacion de contrasena.

Configuracion esperada en el entorno (ver .env.example):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_USE_TLS
"""
import smtplib
from email.mime.text import MIMEText
from os import getenv


def _smtp_config():
    return {
        "host": getenv("SMTP_HOST"),
        "port": int(getenv("SMTP_PORT", "587")),
        "user": getenv("SMTP_USER"),
        "password": getenv("SMTP_PASSWORD"),
        "from_addr": getenv("SMTP_FROM") or getenv("SMTP_USER"),
        "use_tls": getenv("SMTP_USE_TLS", "true").lower() == "true",
    }


def send_email(to: str, subject: str, body: str) -> None:
    config = _smtp_config()
    if not config["host"] or not config["from_addr"]:
        raise RuntimeError(
            "SMTP no esta configurado: definir SMTP_HOST y SMTP_USER/SMTP_FROM en el entorno."
        )

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = config["from_addr"]
    message["To"] = to

    with smtplib.SMTP(config["host"], config["port"]) as server:
        if config["use_tls"]:
            server.starttls()
        if config["user"] and config["password"]:
            server.login(config["user"], config["password"])
        server.sendmail(config["from_addr"], [to], message.as_string())


def send_password_reset_email(to: str, reset_url: str) -> None:
    subject = "Recuperación de contraseña — Camila Viali"
    body = (
        "Hola,\n\n"
        "Recibimos una solicitud para restablecer tu contraseña.\n"
        f"Si fuiste tú, abre este enlace para elegir una nueva contraseña:\n\n{reset_url}\n\n"
        "Este enlace vence en 30 minutos. Si no solicitaste este cambio, "
        "puedes ignorar este correo.\n"
    )
    send_email(to, subject, body)
