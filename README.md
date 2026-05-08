# 🛡️ AWS AI Cybersecurity Portfolio

> A hands-on portfolio of production-grade AI applications built on AWS, focused on cybersecurity use cases.  
> Built after achieving **AWS Certified AI Practitioner** and **AWS Solutions Architect Professional** certifications.

---

## Portfolio Overview

This repository contains 5 progressively complex AI/cloud cybersecurity projects, each introducing new AWS services and AI concepts. Every project is fully deployed on AWS and documented end to end.

| # | Project | Core AI Concept | AWS Services | Status |
|---|---------|----------------|--------------|--------|
| 1 | [Threat Intelligence Chatbot](#project-1) | Prompt Engineering | Bedrock, Lambda, DynamoDB, API Gateway, CloudFront | ✅ Live |
| 2 | [CVE RAG System](#project-2) | RAG + Vector Search | Bedrock, OpenSearch Serverless, Lambda, VPC | ✅ Live |
| 3 | SOC Triage Agent | Agentic AI + Tool Use | Bedrock Agents, Step Functions, GuardDuty | 🔨 Building |
| 4 | Multi-Agent Threat Hunting | Multi-Agent Orchestration | Step Functions, SQS, Bedrock, Athena | 📋 Planned |
| 5 | Red Team Simulation Platform | MCP + Evaluation | Bedrock, MCP, Lambda, Step Functions | 📋 Planned |

---

## Architecture Progression

Each project builds on the last — no resources are wasted, everything carries forward.

```
Project 1 — Foundation
Lambda + API Gateway + Bedrock (Claude) + DynamoDB + CloudFront
        ↓
Project 2 — Add knowledge base
+ OpenSearch Serverless + Titan Embeddings + VPC Endpoints
        ↓
Project 3 — Add autonomy
+ Bedrock Agents + Tool use + GuardDuty + Step Functions
        ↓
Project 4 — Add coordination
+ Multi-agent orchestration + Parallel execution + Shared state
        ↓
Project 5 — Production hardening
+ MCP servers + Evaluation framework + Provisioned concurrency
```

---

## AI Concepts Covered

| Concept | Project | Description |
|---|---|---|
| Prompt Engineering | 1 | System prompts, persona, output structuring, confidence scoring |
| Session Memory | 1 | DynamoDB conversation history, 10-turn context window |
| Embeddings | 2 | Text → 1024-dimensional vectors via Titan Embed v2 |
| Vector Search (kNN) | 2 | Semantic similarity search over CVE database |
| Hybrid Search | 2 | kNN + BM25 simultaneously for best coverage |
| RAG | 2 | Retrieve documents first, generate grounded cited answers |
| Agentic AI | 3 | Claude autonomously selects and calls tools |
| ReAct Loop | 3 | Reason → Act → Observe → Repeat until done |
| Tool Use | 3 | Lambda functions as callable tools for the agent |
| Guardrails | 3 | Constrain agent behaviour, prevent harmful actions |
| Multi-Agent | 4 | Coordinator + specialist agents working in parallel |
| Orchestration | 4 | Step Functions managing agent execution flow |
| MCP | 5 | Model Context Protocol for dynamic tool discovery |
| Evaluation | 5 | LLM-as-judge scoring answer quality |

---

## Project 1 — Threat Intelligence Chatbot <a name="project-1"></a>

**Folder:** `project-1-chatbot/`

A conversational cybersecurity threat intelligence assistant. SOC analysts can query threat actors, CVEs, TTPs, and IOCs in plain English. Claude answers as a Tier-2 SOC analyst with structured output and confidence scoring.

**Key features:**
- Confidence scoring on every response `[HIGH]` `[MEDIUM]` `[LOW]`
- Structured output: Threat Summary | Key IOCs | Recommended Actions
- Session memory — remembers conversation context across turns
- One-click IOC extraction from any response
- Dark-themed React UI served via CloudFront

[→ View Project 1 README](project-1-chatbot/README.md)

---

## Project 2 — CVE RAG System <a name="project-2"></a>

**Folder:** `project-2-cve-rag/`

A Retrieval Augmented Generation system grounding Claude's answers in real CVE data from the NVD. Claude retrieves the most relevant CVEs from a vector database before generating cited answers — no hallucinated CVE IDs.

**Key features:**
- 150+ real CVEs indexed from NVD (RCE, privilege escalation, SQL injection)
- Hybrid search — semantic (kNN) + keyword (BM25) simultaneously
- Grounded answers citing specific CVE IDs and CVSS scores
- Claude explicitly states when information is NOT in the knowledge base
- RAG mode toggle in the same React UI as Project 1
- Private VPC endpoint connectivity — no public internet exposure

[→ View Project 2 README](project-2-cve-rag/README.md)

---

## AWS Services Used Across Portfolio

```
AI/ML:         Amazon Bedrock (Claude, Titan Embeddings)
Storage:       S3, DynamoDB, OpenSearch Serverless
Compute:       Lambda (Python 3.12)
Networking:    VPC, VPC Endpoints, CloudFront, API Gateway
Security:      IAM, Bedrock Guardrails, WAF
Orchestration: Step Functions, EventBridge, SQS
Observability: CloudWatch, X-Ray
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 (backend), TypeScript/React (frontend) |
| AI Models | Claude Sonnet 4.5, Titan Embeddings v2 |
| Vector DB | OpenSearch Serverless (1024-dim kNN) |
| CDN | CloudFront + S3 (private OAC) |
| IDE | Kiro IDE + Kiro CLI |
| OS | Windows 11 |
| Region | AWS us-east-1 |

---

## Certifications

- ✅ AWS Certified AI Practitioner
- ✅ AWS Solutions Architect Professional
- 🔨 AWS Certified Developer — Associate (in progress)

---

## Author

**Y. Memudu** — Cloud & AI Architect  
Building production-grade AI applications on AWS with a focus on cybersecurity.

---

## Repository Structure

```
aws-ai-cybersecurity-portfolio/
├── project-1-chatbot/          ← Threat Intel Q&A Chatbot
│   ├── backend/
│   ├── frontend/
│   ├── docs/
│   └── README.md
├── project-2-cve-rag/          ← CVE RAG System
│   ├── backend/
│   ├── frontend/
│   ├── docs/
│   └── README.md
├── project-3-soc-agent/        ← Coming soon
├── project-4-threat-hunting/   ← Coming soon
├── project-5-red-team/         ← Coming soon
└── README.md                   ← This file
```
