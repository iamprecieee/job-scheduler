#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./setup_ssl.sh)"
  exit 1
fi

ENV_FILE="$(dirname "$0")/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found! Copy deploy/.env.example to deploy/.env and configure it."
    exit 1
fi
source "$ENV_FILE"

# Extract just the DuckDNS subdomain (e.g. 'job-scheduler' from 'job-scheduler.duckdns.org')
DUCKDNS_DOMAIN="${DOMAIN%%.*}"

echo "Updating DuckDNS IP address to match this EC2 instance..."
curl -k "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip="
echo ""

echo "Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx

echo "Configuring SSL with Certbot for $DOMAIN..."
# The --nginx flag automatically edits the nginx.conf to add SSL settings
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $SSL_EMAIL

echo "Restarting Nginx to apply changes..."
systemctl restart nginx

echo "=========================================================="
echo "SSL Setup Complete!"
echo "Certbot has automatically configured Nginx and set up a cron job for renewal."
echo "You can now visit https://$DOMAIN securely."
echo "=========================================================="
