import json
import boto3
import os
from datetime import datetime, timezone

# boto3 clients — these talk to AWS services
# Lambda automatically uses the IAM role's credentials, no keys needed
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

TABLE_NAME = os.environ.get('CHAT_TABLE', 'threat-intel-chat-history')

# This is the most important part of the whole project.
# It defines HOW Claude behaves — think of it as hiring instructions.
# Changing this prompt completely changes the chatbot's personality and rules.
SYSTEM_PROMPT = """You are a Tier-2 SOC analyst assistant specialising in 
cybersecurity threat intelligence. You help security analysts understand 
threats, CVEs, TTPs, and threat actor behaviour.

Rules you must always follow:
1. Always state your confidence level: [HIGH], [MEDIUM], or [LOW]
2. Never invent CVE IDs — if unsure, say so clearly
3. Structure answers as: Threat Summary | Key IOCs | Recommended Actions
4. If asked about anything outside cybersecurity, politely redirect
5. Saying "I don't know" is better than guessing

You are concise, precise, and think like a defender."""


def get_chat_history(session_id):
    """
    Fetch the last 10 messages for this session from DynamoDB.
    This is what gives the chatbot memory — it remembers what
    was said earlier in the same conversation.
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'session_id': session_id})
        if 'Item' in response:
            return response['Item'].get('messages', [])
    except Exception as e:
        print(f"Error fetching history: {e}")
    return []  # Return empty list if no history exists yet


def save_chat_history(session_id, messages):
    """
    Save the updated conversation back to DynamoDB after each message.
    We cap at 10 messages to keep costs low — older messages drop off.
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        messages = messages[-10:]  # Keep only last 10 turns
        table.put_item(Item={
            'session_id': session_id,
            'messages': messages,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        print(f"Error saving history: {e}")


def call_bedrock(messages):
    """
    Send the conversation to Claude and get a response back.
    The 'messages' array is the full conversation history —
    Claude sees everything said so far and replies in context.
    """
    response = bedrock.invoke_model(
        modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1024,
            'system': SYSTEM_PROMPT,  # The hiring instructions
            'messages': messages,      # The full conversation so far
        })
    )
    result = json.loads(response['body'].read())
    return result['content'][0]['text']


def lambda_handler(event, context):
    """
    Main entry point — API Gateway calls this function for every chat message.
    The 'event' contains the HTTP request from the browser.
    The flow is: load history → add new message → call Claude → save → reply
    """

    # Handle CORS preflight — browsers send this before every real request
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {})

    try:
        # Parse the incoming request body
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('session_id', 'default')
        user_message = body.get('message', '').strip()

        if not user_message:
            return cors_response(400, {'error': 'Message cannot be empty'})

        # Step 1 — Load this session's conversation history from DynamoDB
        history = get_chat_history(session_id)

        # Step 2 — Add the user's new message to the history
        history.append({'role': 'user', 'content': user_message})

        # Step 3 — Send the full conversation to Claude
        assistant_reply = call_bedrock(history)

        # Step 4 — Add Claude's reply to the history
        history.append({'role': 'assistant', 'content': assistant_reply})

        # Step 5 — Save the updated conversation back to DynamoDB
        save_chat_history(session_id, history)

        # Step 6 — Return Claude's reply to the browser
        return cors_response(200, {
            'reply': assistant_reply,
            'session_id': session_id,
        })

    except Exception as e:
        print(f"Error: {e}")  # This goes to CloudWatch logs
        return cors_response(500, {'error': 'Internal server error'})


def cors_response(status_code, body):
    """
    Every response needs these CORS headers or the browser will block it.
    This is a browser security feature — not optional.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
        },
        'body': json.dumps(body),
    }