#!/bin/bash

# Define the log file and a temporary file to store new IPs
LOG_FILE="/home/ubuntu/trading_system/logs/nginx_logs/access.log"
TEMP_FILE="/home/ubuntu/trading_system/logs/nginx_logs/new_ips.txt"
PROCESSED_FILE="/home/ubuntu/trading_system/logs/nginx_logs/processed_ips.txt"

# Check if the log file exists and is readable
if [ ! -f "$LOG_FILE" ]; then
    echo "Log file $LOG_FILE does not exist."
    exit 1
fi

if [ ! -r "$LOG_FILE" ]; then
    echo "Log file $LOG_FILE is not readable."
    exit 1
fi

echo "Extracting IPs that returned 400 or 444 status codes..."

# Extract IPs that have returned 400 status code and save them to a temporary file
grep '\-\[400' "$LOG_FILE" > /tmp/grep_400.log
awk -F'-' '{print $2}' /tmp/grep_400.log | tr -d '[]' | sort | uniq > /tmp/temp_ips.log
if [ $? -ne 0 ]; then
    echo "Error extracting IPs with 400 status code"
fi

# Extract IPs that have returned 444 status code and append them to the temporary file
grep '\-\[444' "$LOG_FILE" > /tmp/grep_444.log
awk -F'-' '{print $2}' /tmp/grep_444.log | tr -d '[]' | sort | uniq >> /tmp/temp_ips.log
if [ $? -ne 0 ]; then
    echo "Error extracting IPs with 444 status code"
fi

# Sort and remove duplicates from the temp_ips file
sort /tmp/temp_ips.log | uniq > "$TEMP_FILE"

# Check if the temporary file was created and has content
if [ ! -s "$TEMP_FILE" ]; then
    echo "No IPs found with 400 or 444 status codes."
    exit 1
fi

# Create the processed IPs file if it doesn't exist
if [ ! -f "$PROCESSED_FILE" ]; then
    touch "$PROCESSED_FILE"
fi

# Find new IPs by comparing with processed IPs file
comm -23 "$TEMP_FILE" "$PROCESSED_FILE" > /tmp/new_ips.log

# Check if there are new IPs to process
if [ ! -s /tmp/new_ips.log ]; then
    echo "No new IPs to block."
    rm /tmp/grep_400.log /tmp/grep_444.log /tmp/temp_ips.log /tmp/new_ips.log
    exit 0
fi

# Loop through each new IP and add it to UFW deny rules if not already blocked
while IFS= read -r ip; do
    if ! sudo ufw status | grep -q "$ip"; then
        sudo ufw deny from "$ip"
        echo "Blocked IP: $ip"
    else
        echo "IP $ip is already blocked."
    fi
done < /tmp/new_ips.log

# Append new IPs to the processed IPs file
cat /tmp/new_ips.log >> "$PROCESSED_FILE"

# Clean up temporary files
sudo rm "$TEMP_FILE" /tmp/grep_400.log /tmp/grep_444.log /tmp/temp_ips.log /tmp/new_ips.log

# Reload UFW to apply changes
sudo ufw reload
echo "UFW reloaded."
