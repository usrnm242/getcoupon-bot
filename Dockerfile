FROM python:3

RUN mkdir -p /usr/src/getcoupon_bot

COPY . /usr/src/getcoupon_bot

WORKDIR /usr/src/getcoupon_bot

RUN pip install -r ./requirements.txt

ENTRYPOINT gunicorn -b 0.0.0.0:8686 flask_server:app
