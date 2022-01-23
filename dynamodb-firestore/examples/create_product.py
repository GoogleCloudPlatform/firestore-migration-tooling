# Copyright 2022, Google, Inc.
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

# If you are not using the default profile, remember to export 
# AWS_PROFILE before running. For example:
# export AWS_PROFILE=DDB2Firestore

client = boto3.client('dynamodb')

resp = client.create_table(
  TableName='Product',
  AttributeDefinitions=[
  {
      'AttributeName': 'PK',
      'AttributeType': 'S'
  },
  {
      'AttributeName': 'SK',
      'AttributeType': 'S'
  },
  {
      'AttributeName': 'product_id',
      'AttributeType': 'S'
  },
  {
      'AttributeName': 'product_category',
      'AttributeType': 'S'
  }
  ],
  GlobalSecondaryIndexes=[
    {
       "IndexName": "By_Product_Category", 
          "Projection": {
             "ProjectionType": "ALL"
          }, 
           "ProvisionedThroughput": {
               "WriteCapacityUnits": 5, 
               "ReadCapacityUnits": 5
           }, 
           "KeySchema": [
            {
               "KeyType": "HASH", 
               "AttributeName": "product_category"
            },
            {
               "KeyType": "RANGE", 
               "AttributeName": "product_id"
            }
           ]
         }
  ],
  KeySchema=[
  {
      'AttributeName': 'PK',
      'KeyType': 'HASH'
  },
  {
      'AttributeName': 'SK',
      'KeyType': 'RANGE'
  },
  ],
  ProvisionedThroughput=
  {
      'ReadCapacityUnits': 5,
      'WriteCapacityUnits': 5
  }
)