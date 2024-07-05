#!/bin/bash

sudo apt-get update -y
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update -y
sudo apt-get install -y docker-ce
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ${USER}
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo chmod 666 /var/run/docker.sock
sudo timedatectl set-timezone Asia/Taipei
docker --version
docker-compose --version

cd /home/ubuntu/trading_system
sudo chmod +x block_ips.sh
#block malicious ips hourly 00:30, 01:30....
(crontab -l 2>/dev/null | grep -v "/home/ubuntu/trading_system/block_ips.sh"; echo "30 * * * * /home/ubuntu/trading_system/block_ips.sh") | crontab -

