#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./setup_server.sh)"
  exit 1
fi

ENV_FILE="$(dirname "$0")/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found! Copy deploy/.env.example to deploy/.env and configure it."
    exit 1
fi
source "$ENV_FILE"

echo "Updating system packages..."
apt-get update && apt-get upgrade -y

echo "Installing Nginx, PostgreSQL, Redis, and build dependencies..."
apt-get install -y nginx postgresql postgresql-contrib redis-server curl git build-essential

echo "Installing uv (Python package manager)..."
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

echo "Installing Node.js and npm..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Configure PostgreSQL
echo "Setting up PostgreSQL Database..."
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME:-jobscheduler};" || true
sudo -u postgres psql -c "CREATE USER ${DB_USER:-jobuser} WITH PASSWORD '${DB_PASSWORD:-jobpassword}';" || true
sudo -u postgres psql -c "ALTER ROLE ${DB_USER:-jobuser} SET client_encoding TO 'utf8';" || true
sudo -u postgres psql -c "ALTER ROLE ${DB_USER:-jobuser} SET default_transaction_isolation TO 'read committed';" || true
sudo -u postgres psql -c "ALTER ROLE ${DB_USER:-jobuser} SET timezone TO 'UTC';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME:-jobscheduler} TO ${DB_USER:-jobuser};" || true
# Need to grant schema public privileges in postgres 15+
sudo -u postgres psql -d ${DB_NAME:-jobscheduler} -c "GRANT ALL ON SCHEMA public TO ${DB_USER:-jobuser};" || true

echo "Configuring Nginx with your Domain..."
sed "s/\$DOMAIN/$DOMAIN/g" deploy/nginx.conf > /etc/nginx/sites-available/job-scheduler

echo "Configuring systemd service..."
sed -e "s/\$DB_USER/${DB_USER:-jobuser}/g" \
    -e "s/\$DB_PASSWORD/${DB_PASSWORD:-jobpassword}/g" \
    -e "s/\$DB_NAME/${DB_NAME:-jobscheduler}/g" \
    deploy/job-scheduler.service > /etc/systemd/system/job-scheduler.service

echo "=========================================================="
echo "System dependencies installed!"
echo "Next steps:"
echo "1. Run database migrations: cd /var/www/job-scheduler/backend && DATABASE_URL=\"postgresql+asyncpg://${DB_USER:-jobuser}:${DB_PASSWORD:-jobpassword}@localhost:5432/${DB_NAME:-jobscheduler}\" uv run alembic upgrade head"
echo "2. Build frontend: cd /var/www/job-scheduler/frontend && npm install && VITE_API_BASE_URL=/api/v1 npm run build"
echo "3. Enable services: sudo ln -s /etc/nginx/sites-available/job-scheduler /etc/nginx/sites-enabled/ && sudo systemctl daemon-reload && sudo systemctl enable --now job-scheduler && sudo systemctl reload nginx"
echo "=========================================================="
