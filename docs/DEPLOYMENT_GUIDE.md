# Job Scheduler Deployment Guide

This guide provides a comprehensive, step-by-step workflow for provisioning, securing, and deploying the Job Scheduler application to a production AWS EC2 instance. Follow this guide exactly to replicate a successful deployment.

> [!IMPORTANT]
> Security is prioritized throughout this guide. Do not skip the SSH key permission steps or the SSL generation phases.

---

## 1. Prerequisites

### AWS Configuration
You need the AWS CLI installed and configured with your IAM credentials.

1. **Install AWS CLI**:
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
rm AWSCLIV2.pkg
```
2. **Configure Credentials**:
```bash
aws configure
```
*(You will be prompted for your AWS Access Key ID, Secret Access Key, and default region).*

#### How to get your AWS Credentials:
1. Log in to the [AWS Management Console](https://console.aws.amazon.com/).
2. In the top right corner, click your account name and select **Security Credentials**.
3. Scroll down to the **Access keys** section and click **Create access key**.
4. Select **Command Line Interface (CLI)**, check the confirmation box, and click Next.
5. Click **Create access key**. Copy both the Access Key ID and Secret Access Key (you will only see the secret key once!).
6. For the "Default region name" when running `aws configure`, use `us-east-1` (or whichever region you prefer).

### Create AWS Key Pair
Before provisioning the server, you must create an SSH key pair to securely log in. Run this in your project's root folder:

1. Generate the key pair and save it as a `.pem` file:
```bash
aws ec2 create-key-pair \
    --key-name job-scheduler-key \
    --query 'KeyMaterial' \
    --output text > job-scheduler-key.pem
```

2. Lock down the file permissions (AWS requires this to prevent unprotected private key errors):
```bash
chmod 400 job-scheduler-key.pem
```

> [!TIP]
> If you ever run an `aws` command manually and your terminal fills up with JSON output ending with `(END)`, this is the default AWS pager. Simply **press `q` on your keyboard** to exit the screen and return to your prompt. (We've automatically disabled this in the `provision.sh` script to prevent it from getting stuck!).

## 2. Configuration

Before running any scripts, you must configure your environment variables.

1. Navigate to the `deploy/` directory.
2. Copy the template: `cp .env.example .env`
3. Open `.env` and fill in your DuckDNS token, Email, AWS configuration, and desired Database credentials.

### DuckDNS Setup
1. Go to [DuckDNS.org](https://www.duckdns.org/) and sign in.
2. Create a free domain name (e.g., `job-scheduler.duckdns.org`) and put it in your `.env`.
3. Copy your **Token** and put it in your `.env`.

---

## 3. Infrastructure Provisioning

Run the `provision.sh` script locally. This reads your `.env` file, creates a secure Security Group, and launches a `t3.small` Ubuntu 26.04 instance.

```bash
cd deploy/
./provision.sh
cd ..
```

### Securing the SSH Key
> [!WARNING]  
> AWS will reject your connection if your private key is accessible by others. You must lock down the file permissions.

```bash
chmod 400 <YOUR_KEY_NAME>.pem
```

---

## 4. Secure Code Transfer

We use `rsync` to securely copy the codebase to the server. 

> [!CAUTION]  
> Never copy local virtual environments (`.venv`), node modules, or local cache directories. Doing so will break the server environment.

Run this from your local machine, replacing the IP address with your EC2 Public IP:

```bash
rsync -avz --delete \
  --exclude 'node_modules' \
  --exclude '.venv' \
  --exclude 'backend/.venv' \
  --exclude '.git' \
  --exclude 'dist' \
  --exclude 'backend/.pytest_cache' \
  --exclude 'backend/.ruff_cache' \
  --exclude 'frontend/dist' \
  -e "ssh -i <YOUR_KEY_NAME>.pem" \
  ./ ubuntu@<YOUR_EC2_IP>:~/job-scheduler/
```

---

## 5. Server Setup & Dependencies

SSH into your new instance:
```bash
ssh -i <YOUR_KEY_NAME>.pem ubuntu@<YOUR_EC2_IP>
```

Move the codebase to the standard web directory:
```bash
sudo mkdir -p /var/www/
sudo mv ~/job-scheduler /var/www/
cd /var/www/job-scheduler
```

Run the automated setup script. This installs Node.js, Python (via `uv`), Nginx, and PostgreSQL. **It will automatically read your `deploy/.env` file to create the database securely and configure Nginx and Systemd.**
```bash
sudo ./deploy/setup_server.sh
```

---

## 6. Backend Configuration & Database

The setup script created the PostgreSQL database. Now, install the Python dependencies and create the database tables.

```bash
cd /var/www/job-scheduler/backend

# Install dependencies
uv sync

# Source your configuration and run database migrations dynamically
source /var/www/job-scheduler/deploy/.env
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}" uv run alembic upgrade head
```

---

## 7. Frontend Build

We build the React dashboard using `/api/v1` as the base URL so that it relies on Nginx's relative path proxying.

```bash
cd /var/www/job-scheduler/frontend

# Install Node modules and build
npm install
VITE_API_BASE_URL=/api/v1 npm run build
```

---

## 8. Enabling Services

The `setup_server.sh` script already copied the configured Nginx and Systemd templates to the correct system folders. You just need to enable them:

```bash
# Enable Nginx Site
sudo ln -s /etc/nginx/sites-available/job-scheduler /etc/nginx/sites-enabled/
sudo systemctl reload nginx

# Enable and Start the Backend
sudo systemctl daemon-reload
sudo systemctl enable --now job-scheduler
```

Verify the backend is running without errors:
```bash
systemctl status job-scheduler
```

---

## 9. SSL & Domain Configuration

Run the SSL automation script. This will read your `.env` file, dynamically update DuckDNS with your current EC2 IP address, and use Certbot to provision a free Let's Encrypt SSL certificate.

```bash
cd /var/www/job-scheduler
sudo ./deploy/setup_ssl.sh
```

---

## 10. Final Validation (Mock Email Server)

To ensure email jobs don't throw `Connection Refused` errors, run the mock SMTP server in the background on the production port (`8025`).

```bash
cd /var/www/job-scheduler/backend
nohup uv run python -m aiosmtpd -n -c aiosmtpd.handlers.Debugging -l 127.0.0.1:8025 > email.log 2>&1 &
```

### That's it! 
Navigate to your domain in your browser.
