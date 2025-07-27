cd ~/trading_system
sudo chmod +x block_ips.sh
git pull
sh block_ips.sh
sudo rm trading_system/celerybeat-schedule
docker compose build
docker compose down
# clean up
docker compose up -d
docker container prune -f
docker image prune -f
docker volume prune -f
docker network prune -f
docker system prune -f