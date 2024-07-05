#!/bin/bash

# Define the log file and a temporary file to store new IPs
LOG_FILE="/home/ubuntu/trading_system/logs/nginx_logs/access.log"  # 请将此路径替换为您的实际日志文件路径
TEMP_FILE="/home/ubuntu/trading_system/logs/nginx_logs/blocked_ips.txt"

# Extract IPs that have returned 400 or 444 status code and save them to a temporary file
grep ' 400 ' "$LOG_FILE" | awk -F '[] []' '{print $2}' | sort | uniq > "$TEMP_FILE"
grep ' 444 ' "$LOG_FILE" | awk -F '[] []' '{print $2}' | sort | uniq >> "$TEMP_FILE"
sort "$TEMP_FILE" | uniq > "$TEMP_FILE.sorted"
mv "$TEMP_FILE.sorted" "$TEMP_FILE"

# Loop through each IP and add it to UFW deny rules if not already blocked
while IFS= read -r ip; do
    if ! ufw status | grep -q "$ip"; then
        sudo ufw deny from "$ip"
        echo "Blocked IP: $ip"
    fi
done < "$TEMP_FILE"

# Clean up the temporary file
rm "$TEMP_FILE"

# Reload UFW to apply changes
sudo ufw reload
