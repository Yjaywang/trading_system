FROM python:3.10

WORKDIR /trading_system

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# 安裝 supervisord
RUN apt-get update && apt-get install -y supervisor

# 複製 supervisord 配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 使用 supervisord 啟動所有服務
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]