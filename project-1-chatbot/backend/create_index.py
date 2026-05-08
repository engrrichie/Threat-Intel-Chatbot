import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

ENDPOINT = "https://fksct3ytygbgih1qxdw0.us-east-1.aoss.amazonaws.com"
REGION   = "us-east-1"
INDEX    = "cve-index"

credentials = boto3.Session().get_credentials()
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

index_body = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 512
        }
    },
    "mappings": {
        "properties": {
            "embedding":   {"type": "knn_vector", "dimension": 1536,
                            "method": {"name": "hnsw", "engine": "nmslib", "space_type": "cosinesimil"}},
            "cve_id":      {"type": "keyword"},
            "description": {"type": "text"},
            "severity":    {"type": "keyword"},
            "cvss_score":  {"type": "float"},
            "published":   {"type": "date"},
            "chunk_text":  {"type": "text"},
            "chunk_id":    {"type": "keyword"},
            "source":      {"type": "keyword"}
        }
    }
}

if client.indices.exists(index=INDEX):
    print(f"Index {INDEX} already exists")
else:
    response = client.indices.create(index=INDEX, body=index_body)
    print(f"Index created: {json.dumps(response, indent=2)}")

info = client.indices.get(index=INDEX)
print(f"Index verified: {list(info.keys())}")