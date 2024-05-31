cd /home/ubuntu/trading_system
git pull
docker compose build
docker compose down
docker compose up -d
docker image prune -f