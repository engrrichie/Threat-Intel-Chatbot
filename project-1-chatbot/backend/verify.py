import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

ENDPOINT = "https://fksct3ytygbgih1qxdw0.us-east-1.aoss.amazonaws.com"
REGION   = "us-east-1"
INDEX    = "cve-index"

credentials = boto3.Session().get_credentials().get_frozen_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    "aoss",
    session_token=credentials.token
)
client = OpenSearch(
    hosts=[{"host": ENDPOINT.replace("https://", ""), "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30
)

# Count total documents
count = client.count(index=INDEX)
print(f"Total documents: {count['count']}")

# Count only scored CVEs
scored = client.count(index=INDEX, body={
    "query": {
        "exists": {"field": "cvss_score"}
    }
})
print(f"Scored CVEs (usable): {scored['count']}")

# Search for remote code execution CVEs
result = client.search(index=INDEX, body={
    "query": {"match": {"description": "remote code execution"}},
    "size": 3,
    "_source": ["cve_id", "severity", "cvss_score"]
})
print(f"\nTop 3 remote code execution CVEs:")
for hit in result["hits"]["hits"]:
    src = hit["_source"]
    print(f"  {src['cve_id']} [{src.get('severity','?')}] CVSS: {src.get('cvss_score','?')}")