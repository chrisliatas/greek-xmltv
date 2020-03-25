FROM python:3.7-alpine

WORKDIR /app
# TERM needs to be set here for exec environments
# PIP_TIMEOUT so installation doesn't hang forever
ENV TERM=xterm \
    PIP_TIMEOUT=180
#    PYTHONPATH=$PYTHONPATH:/app \
#    SCRAPY_SETTINGS_MODULE=xmltv.settings

#COPY requirements.txt ./

RUN apk update \
    && apk add --virtual .build-deps gcc openssl-dev python3-dev musl-dev \
    && apk add libffi-dev libxslt-dev jpeg-dev zlib-dev libjpeg curl ca-certificates \
    && update-ca-certificates \
    && pip install scrapyd \
    && apk del .build-deps
#    && pip install --no-cache-dir -r requirements.txt
#    && pip install scrapyd-client \
#    && pip install scrapydweb \

RUN mkdir -p /etc/scrapyd/
COPY scrapyd.conf /etc/scrapyd/
#COPY . .

EXPOSE 6800
CMD ["scrapyd"]