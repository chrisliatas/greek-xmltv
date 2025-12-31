FROM python:3.11-alpine

WORKDIR /app
# TERM needs to be set here for exec environments
# PIP_TIMEOUT so installation doesn't hang forever
ENV TERM=xterm \
    PIP_TIMEOUT=180 \
    PYTHONPATH=/app \
    SCRAPY_SETTINGS_MODULE=xmltv.settings

COPY requirements.txt ./

RUN apk update \
    && apk add --no-cache --virtual .build-deps build-base cargo rust openssl-dev python3-dev musl-dev \
    && apk add --no-cache libffi-dev libxslt-dev jpeg-dev zlib-dev libjpeg curl ca-certificates \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY . .

CMD [ "scrapy", "version" ]
