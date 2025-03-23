FROM --platform=linux/amd64 python:3.11.2-slim

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=config.settings.prod

RUN apt-get -y update && apt-get install -y vim curl

# node.js 설치
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

RUN mkdir /srv/qa-server
ADD . /srv/qa-server

WORKDIR /srv/qa-server

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# node.js 디펜던시 설치
RUN npm install
RUN npm install playwright
RUN npx playwright install-deps
RUN npx playwright install chromium

# 파이썬 기준 모듈 서칭
ENV PYTHONPATH=/srv/qa-server

CMD ["python3", "manage.py", "runserver", "0:8000"]