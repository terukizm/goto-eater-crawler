FROM python:3.8-slim

COPY requirements.txt /tmp
RUN apt-get update && apt-get install -y gcc python-dev \
    && pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

CMD ["python", "-m" "goto_eat_scrapy.main"]
