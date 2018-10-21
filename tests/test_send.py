# -*- coding: utf-8 -*-
import json
from collections import OrderedDict

import mock
import pytest


class Undefined(object):
    def __bool__(self):
        return False


UNDEFINED = Undefined()


def test_mail_configuration(app):
    assert app.mail.state.default_sender == 'sender@example.com'
    assert app.mail.state.server == 'mymailserver.com'
    assert app.mail.state.port == 123
    assert app.mail.state.use_tls == True
    assert app.mail.state.use_ssl == True
    assert app.mail.state.username == 'myusername'
    assert app.mail.state.password == 'mypassword'
    assert app.mail.state.default_sender == 'sender@example.com'
    assert app.mail.state.max_emails == 12345


@pytest.mark.parametrize(
    'value,form_errors,json_errors',
    [
        (
            UNDEFINED,
            ['Missing data for required field.'],
            ['Missing data for required field.'],
        ),
        (
            '',
            ['Not a valid email address.'],
            ['Not a valid email address.'],
        ),
        (
            None,
            ['Missing data for required field.'],
            ['Field may not be null.'],
        ),
        (
            'hello',
            ['Not a valid email address.'],
            ['Not a valid email address.'],
        ),
        (
            'receiver@example.com',
            None,
            None,
        ),
        (
            'привет@мир.рф',
            None,
            None,
        ),
    ],
)
@pytest.mark.parametrize('data_type', (
    'data',
    'json',
))
def test_send_to_field(app, client, outbox, value, form_errors, json_errors,
                       data_type):
    data = {}
    if value is not UNDEFINED:
        data['_sendto'] = value
    res = client.post('/send', **{
        data_type: data,
    })
    errors = json_errors if data_type == 'json' else form_errors
    if errors:
        assert res.status_code == 422
        assert res.json == {
            '_sendto': errors,
        }
        assert len(outbox) == 0
    else:
        assert res.status_code == 200
        assert res.data == b'Form has been successfully sent.'
        assert res.content_type == 'text/plain; charset=utf-8'
        assert len(outbox) == 1
        assert outbox[0].send_to == {value}
        assert outbox[0].sender == app.config['MAIL_DEFAULT_SENDER']
        assert outbox[0].body is None


@pytest.mark.parametrize(
    'send_to',
    (
        'allowed1@example.com',
        'not_allowed@example.com',
    ),
)
@pytest.mark.parametrize('data_type', (
    'data',
    'json',
))
def test_allowed_to_send_only_to_allowed_recipients(app, client, outbox,
                                                    send_to, data_type):
    allowed_recipients = {
        'allowed1@example.com',
        'allowed2@example.com',
    }
    with mock.patch.dict(
            app.config,
            allowed_recipients=allowed_recipients,
    ):
        res = client.post('/send', **{
            data_type: {
                '_sendto': send_to,
            },
        })
        if send_to in allowed_recipients:
            assert res.status_code == 200
            assert res.data == b'Form has been successfully sent.'
            assert res.content_type == 'text/plain; charset=utf-8'
            assert len(outbox) == 1
            assert outbox[0].send_to == {send_to}
        else:
            assert res.status_code == 403
            assert res.json == {
                '_sendto':
                ['The email address is not allowed as a recipient.'],
            }
            assert len(outbox) == 0


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            UNDEFINED,
            None,
        ),
        (
            '',
            ['Not a valid email address.'],
        ),
        (
            None,
            None,
        ),
        (
            'hello',
            ['Not a valid email address.'],
        ),
        (
            'example@example.com',
            None,
        ),
        (
            'привет@мир.рф',
            None,
        ),
    ],
)
@pytest.mark.parametrize('data_type', (
    'data',
    'json',
))
def test_reply_to_field(app, client, outbox, value, errors, data_type):
    data = {
        '_sendto': 'receiver@example.com',
    }
    if value is not UNDEFINED:
        data['_replyto'] = value
    res = client.post('/send', **{
        data_type: data,
    })
    if errors:
        assert res.status_code == 422
        assert res.json == {
            '_replyto': errors,
        }
    else:
        assert res.status_code == 200
        assert res.data == b'Form has been successfully sent.'
        assert res.content_type == 'text/plain; charset=utf-8'
        assert len(outbox) == 1
        expected_reply_to = value or None
        assert outbox[0].reply_to == expected_reply_to


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            UNDEFINED,
            None,
        ),
        (
            '',
            ['Not a valid URL.'],
        ),
        (
            None,
            None,
        ),
        (
            'hello',
            ['Not a valid URL.'],
        ),
        (
            '/hello',
            ['Not a valid URL.'],
        ),
        (
            'http://example.com',
            None,
        ),
        (
            'http://example.com/some/path/?with=args',
            None,
        ),
    ],
)
@pytest.mark.parametrize('referer', (
    UNDEFINED,
    '',
    'http://example.com/form',
))
@pytest.mark.parametrize('data_type', (
    'data',
    'json',
))
def test_next_field(app, client, outbox, value, errors, referer, data_type):
    headers = {}
    if referer is not UNDEFINED:
        headers['Referer'] = referer
    data = {
        '_sendto': 'receiver@example.com',
    }
    if value is not UNDEFINED:
        data['_next'] = value
    res = client.post(
        '/send', **{
            'headers': headers,
            'follow_redirects': False,
            data_type: data,
        })
    if errors:
        assert res.status_code == 422
        assert res.json == {
            '_next': errors,
        }
    else:
        expected_redirect_to = value or referer
        if expected_redirect_to:
            assert res.status_code == 302
            assert res.headers.get('location') == expected_redirect_to
        else:
            assert res.status_code == 200
            assert res.data == b'Form has been successfully sent.'
            assert res.content_type == 'text/plain; charset=utf-8'
        # Check email has been sent.
        assert len(outbox) == 1


@pytest.mark.parametrize(
    'value',
    (
        UNDEFINED,
        '',
        None,
        'hello',
        'привет',
    ),
)
@pytest.mark.parametrize('referer', (
    UNDEFINED,
    '',
    'http://example.com/form',
))
@pytest.mark.parametrize('data_type', (
    'data',
    'json',
))
def test_subject_field(app, client, outbox, value, referer, data_type):
    headers = {}
    if referer is not UNDEFINED:
        headers['Referer'] = referer
    data = {
        '_sendto': 'receiver@example.com',
    }
    if value is not UNDEFINED:
        data['_subject'] = value
    res = client.post(
        '/send', **{
            'headers': headers,
            'follow_redirects': False,
            data_type: data,
        })
    if referer:
        assert res.status_code == 302
        assert res.headers.get('location') == referer
    else:
        assert res.status_code == 200
        assert res.data == b'Form has been successfully sent.'
        assert res.content_type == 'text/plain; charset=utf-8'

    assert len(outbox) == 1
    if value:
        expected_subject = value
    elif referer:
        expected_subject = f'New submission from {referer}'
    else:
        expected_subject = 'New submission'
    assert outbox[0].subject == expected_subject


@pytest.mark.parametrize(
    'value',
    (
        UNDEFINED,
        '',
        None,
        'hello',
        'привет',
        'one, two,three',
    ),
)
@pytest.mark.parametrize('data_type', (
    'data',
    'json',
))
def test_cc_field(app, client, outbox, value, data_type):
    data = {
        '_sendto': 'receiver@example.com',
    }
    if value is not UNDEFINED:
        data['_cc'] = value
    res = client.post('/send', **{
        data_type: data,
    })
    assert res.status_code == 200
    assert res.data == b'Form has been successfully sent.'
    assert res.content_type == 'text/plain; charset=utf-8'
    assert len(outbox) == 1
    expected_cc = value or []
    assert outbox[0].cc == expected_cc


@pytest.mark.parametrize(
    'value',
    [
        UNDEFINED,
        '',
        None,
        'hello',
        'привет',
        'one, two,three',
    ],
)
@pytest.mark.parametrize('data_type', (
    'data',
    'json',
))
def test_gotcha_field(app, client, outbox, value, data_type):
    data = {
        '_sendto': 'receiver@example.com',
    }
    if value is not UNDEFINED:
        data['_gotcha'] = value
    res = client.post('/send', **{
        data_type: data,
    })
    assert res.status_code == 200
    assert res.data == b'Form has been successfully sent.'
    assert res.content_type == 'text/plain; charset=utf-8'
    if value is UNDEFINED or (data_type != 'json' and value is None):
        assert len(outbox) == 1
    else:
        assert len(outbox) == 0


@pytest.mark.parametrize('data_type', (
    'data',
    'json',
))
def test_body(app, client, outbox, data_type):
    data = OrderedDict()
    data['_sendto'] = 'receiver@example.com'
    data['Hello'] = 'World'
    data['привет мир'] = 'привер привет'
    data['empty_field'] = ''
    data['another_field'] = 'hola'
    headers = {}
    if data_type == 'json':
        # We need to construct json data by hand because
        # flask test client enables key ordering. But we need
        # to test that original key ordering is preserved.
        data = json.dumps(data)
        headers['content-type'] = 'application/json'
    res = client.post(
        '/send',
        data=data,
        headers=headers,
    )
    assert res.status_code == 200
    assert res.data == b'Form has been successfully sent.'
    assert res.content_type == 'text/plain; charset=utf-8'
    assert len(outbox) == 1
    expected_body = ('Hello:\n'
                     'World\n'
                     '\n'
                     'привет мир:\n'
                     'привер привет\n'
                     '\n'
                     'empty_field:\n'
                     '\n'
                     '\n'
                     'another_field:\n'
                     'hola')
    assert outbox[0].body == expected_body
