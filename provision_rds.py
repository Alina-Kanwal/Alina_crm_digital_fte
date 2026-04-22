import os
import json
import uuid
from alibabacloud_rds20140815.client import Client as Rds20140815Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_rds20140815 import models as rds_20140815_models

def create_client(access_key_id, access_key_secret, region_id="cn-hangzhou"):
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret
    )
    config.endpoint = f'rds.{region_id}.aliyuncs.com'
    return Rds20140815Client(config)

def create_rds_instance(client, vpc_id, vswitch_id, region_id="cn-hangzhou"):
    create_req = rds_20140815_models.CreateDBInstanceRequest(
        region_id=region_id,
        engine='PostgreSQL',
        engine_version='14.0',
        dbinstance_class='rds.pg.s1.small',
        dbinstance_storage=20,
        dbinstance_net_type='Intranet',
        vpcid=vpc_id,
        v_switch_id=vswitch_id,
        security_iplist='0.0.0.0/0', # Required, set to open for now
        dbinstance_description='Digital FTE Prod',
        pay_type='Postpaid',
        client_token=str(uuid.uuid4())
    )
    
    try:
        response = client.create_dbinstance(create_req)
        return response.body
    except Exception as e:
        print(f"Error creating RDS: {e}")
        return None

def main():
    config_path = r"C:\Users\a\.aliyun\config.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    profile = next(p for p in config['profiles'] if p['name'] == config['current'])
    ak = profile['access_key_id']
    sk = profile['access_key_secret']
    region = profile['region_id']
    
    vpc_id = "vpc-bp1x9l74et99dja73v9yk"
    vswitch_id = "vsw-bp19fnji9nnyy58r3buvt"
    
    print(f"Creating RDS instance in {region}...")
    client = create_client(ak, sk, region)
    result = create_rds_instance(client, vpc_id, vswitch_id, region)
    
    if result:
        print(f"Successfully initiated creation.")
        print(f"Instance ID: {result.dbinstance_id}")
    else:
        print("Failed to initiate creation.")

if __name__ == "__main__":
    main()
