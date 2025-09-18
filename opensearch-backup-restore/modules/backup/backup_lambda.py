import json
import boto3
import requests
from datetime import datetime
import os

def handler(event, context):
    opensearch_endpoint = os.environ['OPENSEARCH_ENDPOINT']
    s3_bucket = os.environ['S3_BUCKET']
    
    # Create snapshot repository if not exists
    repo_name = "s3-snapshot-repo"
    snapshot_name = f"snapshot-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    
    # Register S3 repository
    repo_url = f"https://{opensearch_endpoint}/_snapshot/{repo_name}"
    repo_payload = {
        "type": "s3",
        "settings": {
            "bucket": s3_bucket,
            "region": boto3.Session().region_name,
            "role_arn": get_opensearch_service_role()
        }
    }
    
    try:
        # Register repository
        response = requests.put(repo_url, json=repo_payload, timeout=30)
        print(f"Repository registration: {response.status_code}")
        
        # Create snapshot
        snapshot_url = f"https://{opensearch_endpoint}/_snapshot/{repo_name}/{snapshot_name}"
        snapshot_payload = {
            "indices": "*",
            "ignore_unavailable": True,
            "include_global_state": False
        }
        
        response = requests.put(snapshot_url, json=snapshot_payload, timeout=30)
        print(f"Snapshot creation: {response.status_code}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Snapshot {snapshot_name} created successfully',
                'snapshot_name': snapshot_name
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_opensearch_service_role():
    # Return the service-linked role ARN for OpenSearch
    account_id = boto3.client('sts').get_caller_identity()['Account']
    region = boto3.Session().region_name
    return f"arn:aws:iam::{account_id}:role/aws-service-role/es.amazonaws.com/AWSServiceRoleForAmazonElasticsearchService"