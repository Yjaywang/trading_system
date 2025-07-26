#!/bin/bash

# ==============================================================================
#           System Initialization & Application Environment Setup
# ==============================================================================
#
# DESCRIPTION:
#   This script automates the setup of a new Ubuntu server, including:
#   - System package updates and essential tools installation.
#   - Docker Engine and Docker Compose installation.
#   - SSH and UFW firewall configuration.
#   - System timezone and Cron job setup.
#
# USAGE:
#   ./setup_server.sh
#
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Script Behavior & Configuration
# ------------------------------------------------------------------------------

# Exit on error, treat unset variables as errors, and propagate exit status
# through pipelines.
set -Eeuo pipefail

# --- Script Configuration ---
readonly TIMEZONE="Asia/Taipei"
readonly UFW_SSH_ALLOW_SUBNET="192.168.0.0/16"
readonly CRON_CONTAINER_NAME="trading_system-app-1"
# Note: Regularly restarting a container is often a workaround.
# Investigate the root cause in the application if possible.
readonly CRON_JOB_1="50 13 * * * docker restart ${CRON_CONTAINER_NAME}"
readonly CRON_JOB_2="10 15 * * * docker restart ${CRON_CONTAINER_NAME}"

# ------------------------------------------------------------------------------
# 2. Update System and Install Essentials
# ------------------------------------------------------------------------------
echo "--- Updating system and installing essential tools... ---"
sudo apt-get update -y
sudo apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  openssh-server \
  ufw

# ------------------------------------------------------------------------------
# 3. Install Docker Engine
# ------------------------------------------------------------------------------
echo "--- Installing Docker Engine... ---"
if ! command -v docker &> /dev/null; then
  echo "Setting up Docker GPG key..."
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo "Adding Docker APT repository..."
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  echo "Updating APT repository list and installing Docker..."
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
  echo "Docker is already installed. Skipping installation."
fi

echo "Ensuring Docker service is started and enabled on boot..."
sudo systemctl start docker
sudo systemctl enable docker

echo "Adding current user '${USER}' to the 'docker' group..."
# Check if user is already in the group to avoid unnecessary usermod calls
if ! groups "${USER}" | grep -q '\bdocker\b'; then
  sudo usermod -aG docker "${USER}"
  echo "User added. Please log out and log back in, or run 'newgrp docker'."
else
  echo "User '${USER}' is already in the 'docker' group."
fi

# ------------------------------------------------------------------------------
# 4. Configure SSH Service
# ------------------------------------------------------------------------------
echo "--- Configuring SSH Service... ---"
sudo systemctl start ssh
sudo systemctl enable ssh

# ------------------------------------------------------------------------------
# 5. Configure UFW Firewall
# ------------------------------------------------------------------------------
echo "--- Configuring UFW firewall... ---"
sudo ufw default deny incoming
sudo ufw default allow outgoing
echo "Allowing SSH (port 22) connections from '${UFW_SSH_ALLOW_SUBNET}'..."
sudo ufw allow from "${UFW_SSH_ALLOW_SUBNET}" to any port 22

# Using --force to enable UFW non-interactively
echo "Enabling UFW firewall (non-interactive)..."
sudo ufw --force enable
echo "UFW firewall is active."

# ------------------------------------------------------------------------------
# 6. Set System Timezone
# ------------------------------------------------------------------------------
echo "--- Setting system timezone to '${TIMEZONE}'... ---"
sudo timedatectl set-timezone "${TIMEZONE}"

# ------------------------------------------------------------------------------
# 7. Configure Cron Scheduled Tasks
# ------------------------------------------------------------------------------
# Function to add a cron job if it doesn't already exist
add_cron_job() {
  local job="$1"
  echo "Checking and adding Cron Job: '${job}'"
  # Use a temporary file for safer crontab updates
  crontab -l > /tmp/current_crontab 2>/dev/null || true
  if ! grep -Fq -- "$job" /tmp/current_crontab; then
    echo "$job" >> /tmp/current_crontab
    crontab /tmp/current_crontab
    echo "Cron Job added."
  else
    echo "Cron Job already exists."
  fi
  rm -f /tmp/current_crontab
}

echo "--- Configuring Cron scheduled tasks... ---"
add_cron_job "${CRON_JOB_1}"
add_cron_job "${CRON_JOB_2}"

# ------------------------------------------------------------------------------
# 8. Verify Installation and Configuration
# ------------------------------------------------------------------------------
echo "--- Final Verification Checks ---"
echo ""
echo "Docker Version:"
docker --version
echo ""
echo "Docker Compose Version:"
docker compose version
echo ""
echo "UFW Firewall Status:"
sudo ufw status verbose
echo ""
echo "System Time & Timezone:"
timedatectl status | grep -E "Time zone|System clock synchronized|NTP service|RTC in local TZ"
echo ""
echo "Current Cron Schedule for ${USER}:"
crontab -l | cat
echo ""
echo "------------------------------------------------------------------------------"
echo "✅ Script execution complete."
echo "❗️ IMPORTANT: For Docker permissions to apply, you must LOG OUT and LOG BACK IN,"
echo "   or run the 'newgrp docker' command in your current shell."
echo "🔥 SECURITY: Ensure your SSH connection from '${UFW_SSH_ALLOW_SUBNET}' is working"
echo "   before disconnecting, as the firewall is now active."
echo "------------------------------------------------------------------------------"