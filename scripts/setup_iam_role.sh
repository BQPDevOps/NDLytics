#!/bin/bash

# Role name for the EC2 instance
ROLE_NAME="NDLyticsEC2Role"
INSTANCE_PROFILE_NAME="NDLyticsEC2Profile"

# Create IAM role
aws iam create-role \
    --role-name ${ROLE_NAME} \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'

# Create instance profile
aws iam create-instance-profile --instance-profile-name ${INSTANCE_PROFILE_NAME}

# Add role to instance profile
aws iam add-role-to-instance-profile \
    --instance-profile-name ${INSTANCE_PROFILE_NAME} \
    --role-name ${ROLE_NAME}

# Create and attach ECR policy
aws iam put-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-name ECRAccess \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage"
                ],
                "Resource": "*"
            }
        ]
    }'

# Get instance ID
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)

# Attach role to EC2 instance
aws ec2 associate-iam-instance-profile \
    --instance-id ${INSTANCE_ID} \
    --iam-instance-profile Name=${INSTANCE_PROFILE_NAME}

echo "IAM role and profile created and attached to the instance"