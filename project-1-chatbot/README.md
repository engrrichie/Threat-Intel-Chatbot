# 🛡️ Project 1 — Threat Intelligence Q&A Chatbot

> **AWS AI Cybersecurity Portfolio** · Project 1 of 5  
> Built on AWS using Amazon Bedrock, Lambda, DynamoDB, API Gateway, and CloudFront

---

## What This Is

A production-structured cybersecurity threat intelligence chatbot that lets SOC analysts query threat actors, CVEs, TTPs, and IOCs in plain English. Claude 3.5 Sonnet answers as a Tier-2 SOC analyst with structured output, confidence scoring, and conversation memory.

**Live capabilities:**
- Confidence scoring on every response: `[HIGH]` `[MEDIUM]` `[LOW]`
- Structured output: Threat Summary | Key IOCs | Recommended Actions
- Session memory — remembers conversation context across turns (DynamoDB)
- One-click IOC extraction — IPs, CVE IDs, MITRE ATT&CK IDs, hashes, domains
- Quick-prompt chips for common analyst queries
- Dark-themed React UI served over HTTPS via CloudFront

---

## Architecture

```
Browser (React UI)
    │  HTTPS
    ▼
CloudFront ──────────────────────────────► S3 (private bucket)
    │                                       React build files
    │
API Gateway  POST /chat
    │
    ▼
Lambda (Python 3.12)
    ├──► Amazon Bedrock (Claude Sonnet 4.5) — generates SOC analyst response
    └──► DynamoDB                           — stores 10-turn conversation history
         CloudWatch                         — logs and metrics
```

### AWS Services

| Service | Role |
|---|---|
| Amazon Bedrock | LLM inference via Claude Sonnet 4.5 (inference profile) |
| AWS Lambda | Python 3.12 backend — glues Bedrock + DynamoDB together |
| Amazon DynamoDB | Conversation history keyed by session_id, 10-turn cap |
| Amazon API Gateway | REST endpoint — POST /chat and OPTIONS /chat (CORS) |
| Amazon S3 | React frontend static files (private bucket) |
| Amazon CloudFront | HTTPS CDN — accesses S3 privately via OAC |
| AWS IAM | Least-privilege execution role for Lambda |
| Amazon CloudWatch | Lambda execution logs and metrics |

---

## AI Concepts Applied

| Concept | Implementation |
|---|---|
| **Prompt Engineering** | System prompt defines SOC analyst persona, confidence scoring rules, output format |
| **Output Structuring** | Model instructed to always return Threat Summary / IOCs / Actions |
| **Confidence Calibration** | Model instructed to output [HIGH]/[MEDIUM]/[LOW] per response |
| **Session Memory** | Full conversation history stored in DynamoDB, passed to model each turn |
| **Guardrails via Prompting** | Model instructed to redirect non-security queries rather than hallucinate |

---

## Project Structure

```
project-1-chatbot/
├── backend/
│   ├── lambda_function.py      ← Lambda handler — Bedrock + DynamoDB
│   ├── test_bedrock.py         ← Local Bedrock connectivity test
│   ├── deploy.ps1              ← One-command redeploy script
│   └── iam/
│       ├── lambda-policy.json  ← Least-privilege Bedrock + DynamoDB policy
│       └── trust-policy.json   ← Lambda execution trust policy
├── frontend/
│   └── src/
│       └── App.tsx             ← React TypeScript chat UI
├── docs/
│   └── build-guide.md          ← Complete step-by-step build documentation
└── README.md
```

---

## Quick Start

### 1 — Configure AWS

```powershell
aws configure
# Enter: Access Key ID, Secret Key, region: us-east-1, format: json

aws sts get-caller-identity
# Verify connection
```

### 2 — Enable Bedrock Model Access

AWS Console → Amazon Bedrock → Model access → Modify → tick **Claude Sonnet 4.5** → Submit

### 3 — Deploy Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install boto3

# Create DynamoDB table
aws dynamodb create-table `
  --table-name threat-intel-chat-history `
  --attribute-definitions AttributeName=session_id,AttributeType=S `
  --key-schema AttributeName=session_id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST --region us-east-1

# Create IAM role
aws iam create-role --role-name threat-intel-lambda-role `
  --assume-role-policy-document file://iam/trust-policy.json
aws iam attach-role-policy --role-name threat-intel-lambda-role `
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam put-role-policy --role-name threat-intel-lambda-role `
  --policy-name ThreatIntelPolicy --policy-document file://iam/lambda-policy.json

# Deploy Lambda
.\deploy.ps1
```

### 4 — Create API Gateway

See [`docs/build-guide.md`](docs/build-guide.md) for full API Gateway commands.

### 5 — Deploy Frontend

```powershell
cd frontend
npm install
# Edit src/App.tsx — set API_URL to your API Gateway URL
npm run build
# Deploy to S3 + CloudFront (see build guide)
```

---

## Critical Lessons Learned

**1. PowerShell BOM issue**
Never use `Out-File` for JSON files. Use `[System.IO.File]::WriteAllText` with `[System.Text.UTF8Encoding]::new($false)` — `Out-File` silently adds a BOM that breaks the AWS CLI JSON parser.

**2. API Gateway permission ARN format**
Lambda permissions for API Gateway MUST use `arn:aws:execute-api` — NOT `arn:aws:apigateway`. The wrong format causes a silent 500 with no useful error message.

**3. Bedrock inference profiles**
Newer Claude models require inference profile IDs with a `us.` prefix: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. The IAM policy must allow both the `foundation-model` ARN (wildcard region) and the `inference-profile` ARN.

**4. Springclean resource protection**
Tag all resources with `auto-delete=no` immediately after creation to prevent automated cleanup deletion.

---

## Resource Inventory

| Resource | Value |
|---|---|
| Lambda function | threat-intel-chatbot |
| DynamoDB table | threat-intel-chat-history |
| IAM role | threat-intel-lambda-role |
| S3 bucket | threat-intel-chatbot-ym-2025 |
| AWS Region | us-east-1 |
| Model | us.anthropic.claude-sonnet-4-5-20250929-v1:0 |
| Lambda memory | 512 MB |
| Lambda timeout | 29 seconds |

---

## Cost Estimate

| Service | Monthly cost (dev use) |
|---|---|
| Amazon Bedrock | ~$0.03–0.15 per 100 messages |
| Lambda | Free tier |
| DynamoDB | Free tier |
| API Gateway | Free tier |
| CloudFront + S3 | < $0.10 |
| **Total** | **< $1/month** |

---

## What's Next

Project 2 extends this chatbot with a RAG system — Claude stops answering from training data and instead retrieves real CVEs from your own vector database before generating grounded cited answers.

[→ Project 2: CVE RAG System](../project-2-cve-rag/README.md)
