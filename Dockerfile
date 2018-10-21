FROM python:3.7.0-alpine3.8

RUN mkdir /root/formsend
ADD ./formsend/ /root/formsend/
ADD ./reqs.txt /tmp/
RUN pip install -r /tmp/reqs.txt

WORKDIR /root/formsend
EXPOSE 8000

CMD ["gunicorn", "wsgi:app", "-b", "[::]:8000"]