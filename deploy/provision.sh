#!/bin/bash
set -e

# Disable the AWS CLI pager so the script doesn't pause with (END)
export AWS_PAGER=""

ENV_FILE="$(dirname "$0")/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found! Copy deploy/.env.example to deploy/.env and configure it."
    exit 1
fi
source "$ENV_FILE"

echo "Creating Security Group: $SG_NAME"
SG_ID=$(aws ec2 create-security-group \
    --group-name $SG_NAME \
    --description "Security group for Job Scheduler (SSH, HTTP, HTTPS)" \
    --region $AWS_REGION \
    --query 'GroupId' --output text)

echo "Security Group ID: $SG_ID"

echo "Opening Port 22 (SSH)..."
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp --port 22 --cidr 0.0.0.0/0 \
    --region $AWS_REGION

echo "Opening Port 80 (HTTP)..."
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp --port 80 --cidr 0.0.0.0/0 \
    --region $AWS_REGION

echo "Opening Port 443 (HTTPS)..."
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp --port 443 --cidr 0.0.0.0/0 \
    --region $AWS_REGION

echo "Launching EC2 Instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --region $AWS_REGION \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=JobSchedulerServer}]' \
    --query 'Instances[0].InstanceId' --output text)

echo "Instance ID: $INSTANCE_ID"
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --region $AWS_REGION \
    --output text)

echo "=========================================================="
echo "Provisioning Complete!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "SSH Command: ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo "=========================================================="
