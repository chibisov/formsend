Send html forms to email with ease. It's convenient for static sites without any backend.

## Usage

HTML form:

```html
<form action="http://localhost:5000/send" method="post">
    <input type="text" name="name">
    <input type="email" name="_replyto" required>
    <input type="hidden" name="_sendto" value="ex1@example.com">
    <input type="submit" value="Send">
</form>
```

Ajax request:

```html
<script src="https://ajax.aspnetcdn.com/ajax/jQuery/jquery-3.3.1.min.js"></script>
<script>
    $(function() {
        $.ajax({
            url: "http://localhost:5000/send",
            method: "POST",
            data: {name: "John", _sendto: "ex1@example.com"},
            success: function(result) {
                alert(result);
            }
        });
    })
</script>
```

## Advanced features:

Form inputs can have specially named name-attributes, which alter functionality. They are all prefixed with an underscore.

### _sendto

Email address where to send the submission. Must be in `ALLOWED_RECIPIENTS`.

### _replyto

This value is used for the email's Reply-To field. This way you can directly "Reply" to the email to respond to the person who originally submitted the form.

### _next

By default, after submitting a form the user is redirected to the original page (referer). 
If referer header is not provided (some browsers doesn't send it) a simple page with text `Form has been successfully sent.` is show. With `_next` you can provide an alternative redirect URL.

### _subject

This value is used for the email's subject, so that you can quickly reply to submissions without having to edit the subject line each time.

### _cc

This value is used for the email's CC Field. This lets you send a copy of each submission to another email address. If you want to cc multiple emails, simply make the cc field a list of emails each separated by a comma.

### _gotcha

Add this "honeypot" field to avoid spam by fooling scrapers. If a value is provided, the submission will be silently ignored. The input should be hidden with CSS.

## Deploying

With docker:

```
$ docker run \
  -e ALLOWED_RECIPIENTS=ex1@example.com,ex2@example.com \
  -e MAIL_SENDER=ex3@example.com \
  -e MAIL_SERVER=localhost \
  -e MAIL_PORT=465 \
  -e MAIL_USERNAME=user \
  -e MAIL_PASSWORD=password \
  -e MAIL_USE_TLS=0 \
  -e MAIL_USE_SSL=0 \
  -p 5000:8000 \
  chibisov/formsend:0.0.1
```

By default starts only `1` worker. It could be changed with env variable `WEB_CONCURRENCY`:

```
$ docker run \
  ...
  -e WEB_CONCURRENCY=3 \
  ...
  -p 5000:8000 \
  chibisov/formsend:0.0.1
```

Environment variables:

* `ALLOWED_RECIPIENTS` - allowed email recipients. Required.
* `MAIL_SERVER` - SMTP server. Required.
* `MAIL_PORT` - SMTP port. Default is `25`.
* `MAIL_USE_TLS` - SMTP TLS. Required.
* `MAIL_USE_SSL` - SMTP SSL. Required.
* `MAIL_USERNAME` - SMTP username.
* `MAIL_PASSWORD` - SMTP password.
* `MAIL_SENDER` - email address of the sender. Required.
* `MAIL_MAX_EMAILS` - limit on the number of emails sent in a single connection before reconnecting.

## Development

Running development server:

```shell
$ FLASK_ENV=development \
  ALLOWED_RECIPIENTS=ex1@example.com,ex2@example.com \
  MAIL_SENDER=ex3@example.com \
  MAIL_SERVER=localhost \
  MAIL_USERNAME=user \
  MAIL_PASSWORD=password \
  MAIL_USE_TLS=0 \
  MAIL_USE_SSL=0 \
  tox -e flask -- run
```

For `pdb` working don't set the env variable `FLASK_ENV=development`.

Running tests:

```shell
$ tox -e test
```

Checking code style:

```shell
$ tox -e yapf -- formsend tests -r --diff
```

Fixing code style:

```shell
$ tox -e yapf -- formsend tests -r -i
```

Checking types:

```shell
$ tox -e mypy -- formsend
```

## Docker images:

Build:

```shell
$ docker build -t chibisov/formsend:0.0.1 .
```

Push:

```shell
$ docker push chibisov/formsend:0.0.1
```

## TODO:

* Mail send retry (smtp errors)
* Mail send timeout
* Test ajax handler with CORS (liveserver?)


## Credits

`formsend` is the lightweight and stateless alternative to [formspree](https://github.com/formspree/formspree/).