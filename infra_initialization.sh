#!/bin/bash


sudo apt-get update -y
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release openssh-server ufw
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ${USER}


sudo systemctl start ssh
sudo systemctl enable ssh

sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.0.0/16 to any port 22


sudo timedatectl set-timezone Asia/Taipei
(crontab -l 2>/dev/null; echo "50 13 * * * docker restart trading_system-app-1") | crontab -
(crontab -l 2>/dev/null; echo "10 15 * * * docker restart trading_system-app-1") | crontab -

# check installations and configurations

docker --version
docker compose version
crontab -l
sudo ufw status verbose
sudo timedatectl status
