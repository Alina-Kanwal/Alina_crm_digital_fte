import os
import json
from alibabacloud_rds20140815.client import Client as Rds20140815Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_rds20140815 import models as rds_20140815_models
from alibabacloud_tea_util import models as util_models

def create_client(access_key_id, access_key_secret, region_id="cn-hangzhou"):
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret
    )
    config.endpoint = f'rds.{region_id}.aliyuncs.com'
    return Rds20140815Client(config)

def check_rds_instances(client, region_id="cn-hangzhou"):
    describe_db_instances_request = rds_20140815_models.DescribeDBInstancesRequest(
        region_id=region_id
    )
    try:
        # Use the correct method name without extra underscore
        response = client.describe_db_instances(describe_db_instances_request)
        return response.body.items.dbinstance
    except Exception as e:
        print(f"Error calling describe_db_instances: {e}")
        return []

def main():
    config_path = r"C:\Users\a\.aliyun\config.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    profile = next(p for p in config['profiles'] if p['name'] == config['current'])
    ak = profile['access_key_id']
    sk = profile['access_key_secret']
    region = profile['region_id']
    
    print(f"Checking RDS instances in {region}...")
    client = create_client(ak, sk, region)
    
    # Let's try both common names just in case
    methods = [m for m in dir(client) if 'describe_dbinstance' in m.lower() or 'describe_db_instance' in m.lower()]
    print(f"Available describe methods: {methods}")
    
    # Try the most likely one based on our search
    try:
        req = rds_20140815_models.DescribeDBInstancesRequest(region_id=region)
        # Based on previous check, 'describe_db_instances' exists in dir output but might not be what I thought
        # Wait, previous check for 'describe_db_instances' returned False.
        # Check for 'describe_dbinstances' returned True.
        response = client.describe_dbinstances(req)
        instances = response.body.items.dbinstance
    except Exception as e:
        print(f"Primary attempt failed: {e}")
        instances = []
    
    if not instances:
        print("No RDS instances found.")
    else:
        print(f"Found {len(instances)} instances:")
        for inst in instances:
            print(f"- ID: {inst.dbinstance_id}, Description: {inst.dbinstance_description}, Status: {inst.dbinstance_status}")

if __name__ == "__main__":
    main()
