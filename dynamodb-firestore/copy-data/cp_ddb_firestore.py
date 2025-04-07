# Copyright 2021, Google, Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import sys
import json
import boto3
import time
from datetime import datetime
from decimal import Decimal

from google.cloud import firestore
from google.oauth2 import service_account
from boto3.dynamodb.types import TypeDeserializer

# Initialize DynamoDB client
ddb_client = boto3.client("dynamodb")

# Initialize Firestore client with service account
credentials = service_account.Credentials.from_service_account_file('')
firestore_client = firestore.Client(
    project='',
    database='',
    credentials=credentials
)
# Maximum number of writes that can be passed to a Commit operation in Firestore is 500
limit = 500

def dumps(item: dict) -> str:
    return json.dumps(item, default=default_type_error_handler)

def default_type_error_handler(obj):
    if isinstance(obj, Decimal):
        if obj == obj.to_integral_value():
            return int(obj)
        else:
            return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def copy_table(table_name):
    global ddb_client, firestore_client
    if not ddb_client:
        ddb_client = boto3.client("dynamodb")
        
    res = ddb_client.describe_table(TableName=table_name)
    pk, sk = parse_schema(res)

    scan_kwargs = {
        "Limit": limit,
        "TableName": table_name,
    }
    done = False
    start_key = None
    read_cnt = 0
    write_cnt = 0

    print(f"DDB PK -> Firestore ID")
    while not done:
        if start_key:
            scan_kwargs["ExclusiveStartKey"] = start_key

        response = ddb_client.scan(**scan_kwargs)
        ddb_items = response.get("Items", [])
        read_cnt += response.get("Count", 0)
        fs_docs = convert_items(ddb_items)
        write_batch(fs_docs, table_name, pk, sk)
        write_cnt += len(fs_docs)
        start_key = response.get("LastEvaluatedKey", None)
        done = start_key is None

    print(f"Total items read from DynamoDB: {read_cnt}")
    print(f"Total items written to Firestore: {write_cnt}")

def parse_schema(schema_dict):
    pk = None
    sk = None

    table_dict = schema_dict["Table"]
    key_schema = table_dict["KeySchema"]

    for key in key_schema:
        key_name = key["AttributeName"]
        key_type = key["KeyType"]

        if key_type == "HASH":
            pk = key_name
        if key_type == "RANGE":
            sk = key_name

    return pk, sk

def write_batch(fs_docs, table, pk, sk):
    batch = firestore_client.batch()

    for doc in fs_docs:
        pk_val = doc[pk]
        sk_val = None
        if sk is not None:
            sk_val = doc.get(sk)

        doc_id_val = pk_val if sk_val is None else pk_val + sk_val
        doc_id_hash = hashlib.md5(doc_id_val.encode())
        doc_id_md5 = doc_id_hash.hexdigest()

        print(f"{pk_val} -> {doc_id_md5}")

        doc_ref = firestore_client.collection(table).document(doc_id_md5)
        batch.set(doc_ref, doc)

    batch.commit()

def ddb_deserialize(r, type_deserializer=TypeDeserializer()):
    return type_deserializer.deserialize({"M": r})

def convert_items(db_items):
    fs_docs = []
    for item_dict in db_items:
        item_as_json = dumps(ddb_deserialize(item_dict))
        fs_doc = json.loads(item_as_json)
        fs_docs.append(fs_doc)
    return fs_docs

def list_all_tables():
    """List all tables in DynamoDB and return their names"""
    tables = []
    last_evaluated_table_name = None
    
    while True:
        if last_evaluated_table_name:
            response = ddb_client.list_tables(ExclusiveStartTableName=last_evaluated_table_name)
        else:
            response = ddb_client.list_tables()
            
        tables.extend(response.get('TableNames', []))
        
        last_evaluated_table_name = response.get('LastEvaluatedTableName')
        if not last_evaluated_table_name:
            break
    
    return tables

def migrate_all_tables():
    """Migrate all tables from DynamoDB to Firestore"""
    tables = list_all_tables()
    print(f"Found {len(tables)} tables to migrate")
    total_start_time = time.time()
    
    for table in tables:
        print(f"\nStarting migration of table: {table} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        table_start_time = time.time()
        try:
            copy_table(table)
            table_end_time = time.time()
            duration = table_end_time - table_start_time
            print(f"Successfully migrated table: {table}")
            print(f"Time taken: {duration:.2f} seconds")
        except Exception as e:
            print(f"Error migrating table {table}: {str(e)}")
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    print(f"\nTotal migration time: {total_duration:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If table name is provided, migrate specific table
        table_name = sys.argv[1]
        copy_table(table_name)
    else:
        # If no table name provided, migrate all tables
        migrate_all_tables()