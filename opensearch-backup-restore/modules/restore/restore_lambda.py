import json
import boto3
import requests
from datetime import datetime
import os
import time

def handler(event, context):
    opensearch_endpoint = os.environ['OPENSEARCH_ENDPOINT']
    s3_bucket = os.environ['S3_BUCKET']
    repo_name = "s3-snapshot-repo"
    
    try:
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
        
        response = requests.put(repo_url, json=repo_payload, timeout=30)
        print(f"Repository registration: {response.status_code}")
        
        # Get latest snapshot
        snapshots_url = f"https://{opensearch_endpoint}/_snapshot/{repo_name}/_all"
        response = requests.get(snapshots_url, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get snapshots: {response.text}")
        
        snapshots = response.json().get('snapshots', [])
        if not snapshots:
            raise Exception("No snapshots found")
        
        # Sort by start_time and get latest
        latest_snapshot = sorted(snapshots, key=lambda x: x['start_time'], reverse=True)[0]
        snapshot_name = latest_snapshot['snapshot']
        
        print(f"Latest snapshot: {snapshot_name}")
        
        # Close all indices before restore
        close_url = f"https://{opensearch_endpoint}/_all/_close"
        requests.post(close_url, timeout=30)
        
        # Restore snapshot
        restore_url = f"https://{opensearch_endpoint}/_snapshot/{repo_name}/{snapshot_name}/_restore"
        restore_payload = {
            "indices": "*",
            "ignore_unavailable": True,
            "include_global_state": False,
            "rename_pattern": "(.+)",
            "rename_replacement": "restored_$1"
        }
        
        response = requests.post(restore_url, json=restore_payload, timeout=30)
        print(f"Restore initiated: {response.status_code}")
        
        # Wait for restore to complete
        time.sleep(10)
        
        # Check restore status
        status_url = f"https://{opensearch_endpoint}/_recovery"
        response = requests.get(status_url, timeout=30)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Restore from {snapshot_name} completed',
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
    account_id = boto3.client('sts').get_caller_identity()['Account']
    region = boto3.Session().region_name
    return f"arn:aws:iam::{account_id}:role/aws-service-role/es.amazonaws.com/AWSServiceRoleForAmazonElasticsearchService"