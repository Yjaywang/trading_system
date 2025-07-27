cd ~/trading_system
git pull
docker compose build
docker compose down
# clean up
docker compose up -d
docker container prune -f
docker image prune -f
docker volume prune -f
docker network prune -f
docker system prune -f