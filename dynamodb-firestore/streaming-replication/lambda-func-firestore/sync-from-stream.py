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

import boto3
import hashlib
import os
import json
import base64

from google.oauth2 import service_account
from google.cloud import firestore
from boto3.dynamodb.types import TypeDeserializer
from decimal import Decimal


# Initialize clents for AWS
local_dynamodb_client = boto3.client("dynamodb")
secrets_client = boto3.client("secretsmanager")

# Load the GCP credential from AWS secrets manager.
# You need to create the GCP service account key file first
# and upload it to AWS secrets manager.
kwargs = {"SecretId": os.environ["AWS_SECRET_ARN"]}
sa_key_val = secrets_client.get_secret_value(**kwargs)
json_account_info = json.loads(base64.b64decode(sa_key_val["SecretString"]))
sa_credentials = service_account.Credentials.from_service_account_info(
    json_account_info
)

# Initialize clint for Firestore
firestore_client = firestore.Client(credentials=sa_credentials)


def dumps(item: dict) -> str:
    return json.dumps(item, default=default_type_error_handler)


def default_type_error_handler(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


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
            # print('pk: ' + pk)
        if key_type == "RANGE":
            sk = key_name
            # print('sk: ' + sk)
    return pk, sk


def write_batch(fs_docs, table, pk, sk, is_delete=False):
    batch = firestore_client.batch()
    for doc in fs_docs:
        # print(doc)
        pk_val = doc[pk]
        # print('pk_val: ' + pk_val)
        if sk is not None:
            sk_val = doc[sk]
            # print('sk_val: ' + sk_val)

        doc_id = pk_val if sk_val is None else pk_val + sk_val
        # print('doc_id: ' + doc_id)
        doc_id_hash = hashlib.md5(doc_id.encode())
        doc_id_md5 = doc_id_hash.hexdigest()
        # print('doc_id_md5: ' + doc_id_md5)

        doc_ref = firestore_client.collection(table).document(doc_id_md5)
        if is_delete:
            batch.delete(doc_ref)
        else:
            batch.set(doc_ref, doc)

    batch.commit()

def ddb_deserialize(r, type_deserializer=TypeDeserializer()):
    return type_deserializer.deserialize({"M": r})


def convert_items(db_items):
    fs_docs = []

    for item in db_items:
        item_as_json = dumps(ddb_deserialize(item))
        fs_doc = json.loads(item_as_json)
        fs_docs.append(fs_doc)
    return fs_docs


def lambda_handler(event, context):
    table_name = os.environ["DYNAMODB_TABLE_NAME"]

    res = local_dynamodb_client.describe_table(TableName=table_name)
    pk, sk = parse_schema(res)

    ddb_add_records = []
    ddb_del_records = []

    for rec in event["Records"]:
        if rec["eventName"] in ["INSERT", "MODIFY"]:
            add_rec = rec["dynamodb"]["NewImage"]
            add_rec[pk] = rec["dynamodb"]["Keys"][pk]
            add_rec[sk] = rec["dynamodb"]["Keys"][sk]
            ddb_add_records.append(add_rec)

        elif rec["eventName"] == "REMOVE":
            del_rec = rec["dynamodb"]["OldImage"]
            del_rec[pk] = rec["dynamodb"]["Keys"][pk]
            del_rec[sk] = rec["dynamodb"]["Keys"][sk]
            ddb_del_records.append(del_rec)

    fs_add_docs = convert_items(ddb_add_records)
    write_batch(fs_add_docs, table_name, pk, sk)
    write_cnt = len(fs_add_docs)

    fs_del_docs = convert_items(ddb_del_records)
    write_batch(fs_del_docs, table_name, pk, sk, True)
    delete_cnt = len(fs_del_docs)

    print(f"Total items synced to Firestore: {write_cnt}")
    print(f"Total items removed in Firestore: {delete_cnt}")
