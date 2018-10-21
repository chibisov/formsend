# -*- coding: utf-8 -*-
import pytest

from formsend.app import create_app


@pytest.fixture
def app():
    return create_app(
        allowed_recipients={
            'receiver@example.com',
            'привет@мир.рф',
        },
        # Do not send mail in testing.
        mail_suppress_send=True,
        mail_server='mymailserver.com',
        mail_port=123,
        mail_use_tls=True,
        mail_use_ssl=True,
        mail_username='myusername',
        mail_password='mypassword',
        mail_sender='sender@example.com',
        mail_max_emails=12345,
    )


@pytest.fixture
def outbox(app):
    with app.mail.record_messages() as outbox:
        yield outbox
