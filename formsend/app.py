# -*- coding: utf-8 -*-
import json
from functools import wraps
from typing import MutableSet, Optional, Dict, Iterable

import werkzeug.datastructures
from flask import Flask, jsonify, Response, request, current_app, redirect
from flask_mail import Mail, Message
from flask_cors import cross_origin
from marshmallow import Schema, fields, INCLUDE, ValidationError


def create_app(
        allowed_recipients: MutableSet[str],
        mail_server: str,
        mail_port: int,
        mail_use_tls: bool,
        mail_use_ssl: bool,
        mail_username: str,
        mail_password: str,
        mail_sender: str,
        mail_max_emails: int = None,
        mail_suppress_send: bool = False,
) -> Flask:
    app = Flask(__name__)

    # Set configuration.
    app.config.update({
        "allowed_recipients": allowed_recipients,
        "MAIL_SERVER": mail_server,
        "MAIL_PORT": mail_port,
        "MAIL_USE_TLS": mail_use_tls,
        "MAIL_USE_SSL": mail_use_ssl,
        "MAIL_USERNAME": mail_username,
        "MAIL_PASSWORD": mail_password,
        "MAIL_DEFAULT_SENDER": mail_sender,
        "MAIL_MAX_EMAILS": mail_max_emails,
        "MAIL_SUPPRESS_SEND": mail_suppress_send,
    })

    # Init mail sender.
    app.mail = Mail(app)

    # Add routes.
    app.route("/send", methods=["POST"])(send)

    return app


class SendRequestSchema(Schema):
    _sendto = fields.Email(required=True)
    _replyto = fields.Email(allow_none=True)
    _next = fields.Url(allow_none=True)
    _subject = fields.String(allow_none=True)
    _cc = fields.String(allow_none=True)
    _gotcha = fields.String(allow_none=True)

    class Meta:
        unknown = INCLUDE


def ordered_storage(f):
    """
    By default Flask doesn't maintain order of form arguments.
    From: https://gist.github.com/cbsmith/5069769
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        request.parameter_storage_class = (
            werkzeug.datastructures.ImmutableOrderedMultiDict)
        return f(*args, **kwargs)

    return wrapper


@cross_origin(allow_headers=["Accept", "Content-Type"])
@ordered_storage
def send():
    request_schema = SendRequestSchema()
    data_source = request.form or request.json or {}
    try:
        data = request_schema.load(data_source)
    except ValidationError as e:
        current_app.logger.info("Submission rejected: %s",
                                json.dumps(e.messages))
        res = jsonify(e.messages)
        res.status_code = 422
        return res

    # Validate recipients.
    send_to = data.get("_sendto")
    if send_to not in current_app.config["allowed_recipients"]:
        errors = {
            "_sendto": ["The email address is not allowed as a recipient."]
        }
        current_app.logger.info("Submission rejected %s", json.dumps(errors))
        res = jsonify(errors)
        res.status_code = 403
        return res

    referer = request.headers.get("referer")

    is_spam = "_gotcha" in data
    if is_spam:
        current_app.logger.info("Submission rejected: %s", data.get("_gotcha"))
    else:
        if data.get("_subject"):
            subject = data.get("_subject")
        elif referer:
            subject = f"New submission from {referer}"
        else:
            subject = "New submission"
        msg = Message(
            subject=subject,
            reply_to=data.get("_replyto"),
            body=_build_message_body(
                data,
                request_schema.fields,
                # We use keys from original data source for preserving
                # the original fields ordering.
                keys=data_source.keys(),
            ),
            recipients=[send_to],
            cc=data.get("_cc"),
        )
        current_app.mail.send(msg)
        current_app.logger.info("Submitted.")

    # Redirect if needed.
    redirect_to = data.get("_next") or referer
    if redirect_to:
        return redirect(redirect_to)

    return Response("Form has been successfully sent.", mimetype="text/plain")


def _build_message_body(data: Dict, system_fields: Iterable[str],
                        keys: Iterable[str]) -> Optional[str]:
    result = ""
    for key in keys:
        if key in system_fields:
            continue
        if key in data:
            result += f"{key}:\n{data[key]}\n\n"
    if result:
        return result.strip()
    return None
