FROM python:3.10

WORKDIR /trading_system

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y supervisor

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]