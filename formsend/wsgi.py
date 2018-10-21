# -*- coding: utf-8 -*-
import logging

from environs import Env
try:
    from app import create_app
except ImportError:
    from formsend.app import create_app

env = Env()
# Read .env into os.environ
env.read_env()

app = create_app(
    allowed_recipients=env.list('ALLOWED_RECIPIENTS', subject=set),
    mail_server=env.str('MAIL_SERVER'),
    mail_port=env.int('MAIL_PORT', 25),
    mail_use_tls=env.bool('MAIL_USE_TLS'),
    mail_use_ssl=env.bool('MAIL_USE_SSL'),
    mail_username=env.str('MAIL_USERNAME', default=None),
    mail_password=env.str('MAIL_PASSWORD', default=None),
    mail_sender=env.str('MAIL_SENDER'),
    mail_max_emails=env.int('MAIL_MAX_EMAILS', default=None),
)
app.logger.setLevel(logging.INFO)
