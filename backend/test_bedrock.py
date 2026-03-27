import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

response = bedrock.invoke_model(
    modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 200,
        'messages': [
            {
                'role': 'user',
                'content': 'What is CVE-2021-44228 in two sentences?'
            }
        ]
    })
)

result = json.loads(response['body'].read())
print(result['content'][0]['text'])