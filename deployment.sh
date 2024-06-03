cd /home/ubuntu/trading_system
git pull
sudo rm trading_system/celerybeat-schedule
docker compose build
docker compose down
docker compose up -d
docker image prune -f