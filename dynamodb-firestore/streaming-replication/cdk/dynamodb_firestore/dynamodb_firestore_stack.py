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

from aws_cdk import (
    aws_lambda,
    aws_dynamodb,
    aws_sqs,
    aws_secretsmanager,
    aws_iam,
    Duration,
    Stack,
)
from constructs import Construct
from aws_cdk.aws_lambda_event_sources import DynamoEventSource, SqsDlq

import boto3
import os


class DynamodbFirestoreStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the table name from the environment variable
        ddb_table_name = os.environ["DYNAMODB_TABLE"]
        # Get the secret ARN for the GCP service account
        aws_secret_arn = os.environ["SECRET_ARN"]

        # Use boto3 to get the table stream
        dynamodb = boto3.resource('dynamodb')
        ddb_table = dynamodb.Table(ddb_table_name)
        ddb_table_stream_arn = ddb_table.latest_stream_arn

        # Need to use the from_table_attributes method since we use the stream later
        table_cdk = aws_dynamodb.Table.from_table_attributes(
            self,
            "sync-table",
            table_name=ddb_table_name,
            table_stream_arn=ddb_table_stream_arn
        )

        sync_lambda = aws_lambda.DockerImageFunction(
            self, "db-sync-function",
            function_name="ddb-firestore-sync-func",
            memory_size=1024,
            timeout=Duration.seconds(300),
            code=aws_lambda.DockerImageCode.from_image_asset("../lambda-func"))
        sync_lambda.add_environment("DYNAMODB_TABLE_NAME", ddb_table_name)
        sync_lambda.add_environment("AWS_SECRET_ARN", aws_secret_arn)

        dead_letter_queue = aws_sqs.Queue(self, "deadLetterQueue")
        sync_lambda.add_event_source(
            DynamoEventSource(table_cdk,
                              starting_position=aws_lambda.StartingPosition.TRIM_HORIZON,
                              batch_size=500,
                              bisect_batch_on_error=True,
                              on_failure=SqsDlq(
                                  dead_letter_queue),
                              retry_attempts=10
                              ))

        sync_lambda.role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name(
            "SecretsManagerReadWrite"))
        sync_lambda.role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name(
            "AmazonDynamoDBReadOnlyAccess"))
        sync_lambda.role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name(
            "AWSLambdaInvocation-DynamoDB"))
        # secret = aws_secretsmanager.Secret.from_secret_attributes(
        #     self,
        #     "gcp_sa_secret",
        #     secret_partial_arn=aws_secret_arn
        # )
        # secret.grant_read(sync_lambda.role)
