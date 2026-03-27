# Threat Intel Chatbot — Project Context

## What we're building
A cybersecurity threat intelligence Q&A chatbot using:
- Backend: Python Lambda on AWS
- AI: Amazon Bedrock (Claude 3.5 Sonnet)
- Database: DynamoDB for chat history
- Frontend: React

## Stack conventions
- Python 3.12 for all Lambda functions
- boto3 for AWS SDK calls
- All AWS resources in us-east-1
- Follow least-privilege IAM at all times

## Security rules
- Never hardcode AWS credentials
- Always use environment variables for config
- All responses must include CORS headers