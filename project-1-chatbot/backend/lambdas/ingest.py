import boto3
import json
import urllib.request
import hashlib
from botocore.config import Config
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

ENDPOINT       = "https://fksct3ytygbgih1qxdw0.us-east-1.aoss.amazonaws.com"
INDEX          = "cve-index"
REGION         = "us-east-1"
EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"
NVD_URL        = "https://services.nvd.nist.gov/rest/json/cves/2.0/?resultsPerPage=50&keywordSearch=sql%20injection&cvssV3Severity=CRITICAL"
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    config=Config(
        retries={"max_attempts": 3, "mode": "adaptive"},
        connect_timeout=10,
        read_timeout=60
    )
)


def get_opensearch_client():
    credentials = boto3.Session().get_credentials().get_frozen_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        REGION,
        "aoss",
        session_token=credentials.token
    )
    return OpenSearch(
        hosts=[{"host": ENDPOINT.replace("https://", ""), "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=60
    )


def fetch_cves():
    print("Fetching CVEs from NVD...")
    req = urllib.request.Request(
        NVD_URL,
        headers={"User-Agent": "CVE-RAG-System/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
    cves = data.get("vulnerabilities", [])
    print(f"Fetched {len(cves)} CVEs")
    return cves


def extract_cve_text(cve_item):
    cve = cve_item.get("cve", {})
    cve_id = cve.get("id", "UNKNOWN")
    descriptions = cve.get("descriptions", [])
    description = next(
        (d["value"] for d in descriptions if d.get("lang") == "en"),
        "No description available"
    )
    metrics = cve.get("metrics", {})
    cvss_score = None
    severity = "UNKNOWN"
    for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
        if version in metrics and metrics[version]:
            cvss_data = metrics[version][0].get("cvssData", {})
            cvss_score = cvss_data.get("baseScore")
            severity = metrics[version][0].get("baseSeverity",
                       cvss_data.get("baseSeverity", "UNKNOWN"))
            break
    published = cve.get("published", "")[:10]
    chunk_text = (
        f"CVE ID: {cve_id}\n"
        f"Severity: {severity}\n"
        f"CVSS Score: {cvss_score}\n"
        f"Published: {published}\n"
        f"Description: {description}"
    )
    return {
        "cve_id":      cve_id,
        "description": description,
        "severity":    severity.upper(),
        "cvss_score":  cvss_score,
        "published":   published if published else None,
        "chunk_text":  chunk_text,
        "chunk_id":    hashlib.md5(chunk_text.encode()).hexdigest(),
        "source":      "NVD"
    }


def embed_text(text):
    if not text or len(text.strip()) < 10:
        return None
    response = bedrock.invoke_model(
        modelId=EMBED_MODEL_ID,
        body=json.dumps({"inputText": text[:8000]})
    )
    result = json.loads(response["body"].read())
    embedding = result.get("embedding")
    if not embedding:
        return None
    return embedding


def index_document(client, doc):
    client.index(index=INDEX, body=doc)


def lambda_handler(event, context):
    print("Starting CVE ingestion pipeline...")
    client  = get_opensearch_client()
    cves    = fetch_cves()
    success = 0
    errors  = 0

    for cve_item in cves:
        try:
            doc = extract_cve_text(cve_item)
            # Skip rejected CVEs
            vuln_status = cve_item.get("cve", {}).get("vulnStatus", "")
            if vuln_status == "Rejected":
                print(f"Skipping {doc['cve_id']} - rejected CVE")
                continue

            if doc["published"] and doc["published"] < "2000-01-01":
                print(f"Skipping {doc['cve_id']} - too old")
                continue

            if len(doc["description"]) < 20:
                print(f"Skipping {doc['cve_id']} - description too short")
                continue

            embedding = embed_text(doc["chunk_text"])
            if not embedding:
                print(f"Skipping {doc['cve_id']} - no embedding returned")
                continue

            doc["embedding"] = embedding
            index_document(client, doc)
            success += 1
            print(f"Indexed: {doc['cve_id']} [{doc['severity']}]")

        except Exception as e:
            errors += 1
            print(f"Error processing {cve_item.get('cve', {}).get('id', 'UNKNOWN')}: {e}")

    result = {
        "statusCode": 200,
        "processed":  success,
        "errors":     errors,
        "total":      len(cves)
    }
    print(f"Ingestion complete: {json.dumps(result)}")
    return result


if __name__ == "__main__":
    lambda_handler({}, None)