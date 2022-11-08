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

from google.cloud import datastore
from boto3.dynamodb.types import TypeDeserializer
from decimal import Decimal

ddb_client = boto3.client("dynamodb")
datastore_client = datastore.Client()
# Maximum number of writes that can be passed
# to a Commit operation in Datastore is 500
limit = 500


def dumps(item: dict) -> str:
    return json.dumps(item, default=default_type_error_handler)


def default_type_error_handler(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


def copy_table(table_name):

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

    print(f"DDB PK -> Datastore ID")
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
    print(f"Total items written to Datastore: {write_cnt}")


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

    batch = datastore_client.batch()
    batch.begin()

    for doc in fs_docs:
        pk_val = doc[pk]

        if sk is not None:
            sk_val = doc[sk]

        doc_id_val = pk_val if sk_val is None else pk_val + sk_val
        doc_id_hash = hashlib.md5(doc_id_val.encode())
        doc_id_md5 = doc_id_hash.hexdigest()

        print(f"{pk_val} -> {doc_id_md5}")

        entity = datastore.Entity(datastore_client.key(table, doc_id_md5))
        entity.update(doc)
        batch.put(entity)

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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Please provide a DynamoDB table name.")

    table_name = sys.argv[1]
    copy_table(table_name)
