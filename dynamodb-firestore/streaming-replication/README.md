
# Streaming changes from DynamoDB to Firestore

Build and deploy a Lambda function to read the changes from the DynamoDB stream of
a DynamoDB table. The Lambda function will populate the changes to Google Firestore.

If you haven't, you need to [install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) AWS CLI and [create an access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey) for your AWS IAM admin user. You also need the Docker tooling to build a container image.

For simplicity, you can run the following steps in Google Cloud Shell.

## Configuring AWS access

1. Install AWS CLI in Cloud Shell.
    ```bash
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    ```

    Note: Since Cloud Shell will not save files except those under your home directly, you may have to reinstall the tool if you have a new Cloud Shell instance.

1. Ensure you have the access key ID and the secret access key for the AWS IAM user you are using. If you don't, you can use [the steps](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-prereqs.html) in the AWS CLI doc to create them. If you don't want to use an admin user, you can use an IAM user with sufficient permissions for DynamoDB.
\

1.  In Cloud Shell, configure the AWS Command Line Interface (CLI).

    ```bash
    aws configure
    ```
1.  The following output appears:

    ```
    $aws configure  
    AWS Access Key ID [None]: **PASTE_YOUR_ACCESS_KEY_ID**  
    AWS Secret Access Key [None]: **PASTE_YOUR_SECRET_ACCESS_KEY**  
    Default region name [None]: us-east-1  
    Default output format [None]:
    ```

1.  Enter the **ACCESS KEY ID** and **SECRET ACCESS KEY** from the AWS IAM account that you created.
    
    In the **Default region name** field, enter the region you want to use, for example, `us-east-1`. Leave other fields at their default values.

### Creating an AWS IAM role for AWS Lambda

```bash
aws iam create-role --role-name AWSLambdaDynamoDBExecutionRole \
--assume-role-policy-document \
'{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
```

```bash
aws iam attach-role-policy --role-name AWSLambdaDynamoDBExecutionRole \
--policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaInvocation-DynamoDB

aws iam attach-role-policy --role-name AWSLambdaDynamoDBExecutionRole \
--policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess

aws iam attach-role-policy --role-name AWSLambdaDynamoDBExecutionRole \
--policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

## Building and Deploying the AWS Lambda Function

### Building the Lambda 

You need to build a container image for the Lambda function since certain native libraries are not available in the default Lambda runtimes.

1. Set up the variables.
    ```bash
    export AWS_REGION=us-east-1
    export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    export DYNAMODB_TABLE=[Your DynamoDB table name]
    export GCP_PROJECT_ID=[Your GCP Project ID]
    export APP_NAME=ddb-firestore-sync-app
    export AWS_SECRET_NAME=ddb2firestore/gcp-sa-key
    ```
1. Change to the Lambda source directory.
    ```bash
    cd lambda-func
    ```

1. Build the docker image for the Lambda function.
    ```bash
    docker build -t $APP_NAME .
    ```

1. Login to AWS ECR.
    ```bash
    aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    ```

1. Tag the image.
    ```bash
    docker tag ${APP_NAME}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}:latest
    ```

1. Push the image.
    ```bash
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${$APP_NAME}:latest
    ```

### Granting permissions to the Lambda function for GCP resources.

1. Create a service account on GCP and download the key file. 
    ```bash
    gcloud iam service-accounts create dynamodb-firestore-sa \
        --description="SA used to copy records from AWS to GCP" \
        --display-name="dynamodb-firestore-sa"

    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:dynamodb-firestore-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/datastore.user"

    gcloud iam service-accounts keys create gcp-key.json \
        --iam-account=dynamodb-firestore-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com
    ```

1. Create a secret in AWS secrets manager for the GCP service account key file:
    ```bash
    aws secretsmanager create-secret --name $AWS_SECRET_NAME \
    --description "Access GCP firestore" --secret-string $(base64 gcp-key.json)
    ```

### Creating the Lambda function

In this step, you deploy the Lambda function `sync-dbs` with 1GB RAM and 5-minute timeout. You can change those values based on your use case.

```bash
aws lambda create-function --region $AWS_REGION --function-name sync-dbs\
    --package-type Image \
    --timeout 300 \
    --memory-size 1024 \
    --code ImageUri=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${$APP_NAME}:latest \
    --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/AWSLambdaDynamoDBExecutionRole \
    --environment "Variables={DYNAMODB_TABLE_NAME=$DYNAMODB_TABLE}"
```

### Enabling DynamoDB stream

If streaming is not enabled for the DynamoDB table, you need to enable it.

```bash
aws dynamodb update-table --table-name $DYNAMODB_TABLE \
--stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

### Configuring the DynamoDB stream as the event source for the Lambda function:

```bash
aws lambda create-event-source-mapping --function-name sync-dbs \
--batch-size 500 --starting-position LATEST \
--event-source-arn $(aws dynamodbstreams list-streams \
--table-name $DYNAMODB_TABLE --query 'Streams[0].StreamArn' --output text)
```

## Testing and verifying

Finally, you can go to the [DynamoDB console](https://console.aws.amazon.com/dynamodbv2/home?r#tables) to make some changes (add/delete/update) and verify the changes are replicated in the [Firestore database](https://console.cloud.google.com/firestore/data).

## Cleaning up

1. Delete the Lambda function.

    ```bash
    aws lambda delete-function --function-name sync-dbs
    ```

1. Delete the GCP service account secret.

    ```bash
    aws secretsmanager  delete-secret --secret-id $AWS_SECRET_NAME
    ```

1. Delete the ECR repository. All the container images in the repository will be removed as well.

    ```bash
    aws ecr delete-repository --repository-name sync-app --force
    ```

1. Detach the role policies and delete the IAM role.

    ```bash
    aws iam detach-role-policy --role-name AWSLambdaDynamoDBExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaInvocation-DynamoDB

    aws iam detach-role-policy --role-name AWSLambdaDynamoDBExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess

    aws iam detach-role-policy --role-name AWSLambdaDynamoDBExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

    aws iam detach-role-policy --role-name AWSLambdaDynamoDBExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaDynamoDBExecutionRole

    aws iam delete-role --role-name AWSLambdaDynamoDBExecutionRole
    ```

1. Delete the GCP service account.

    ```bash
    gcloud iam service-accounts delete \
        dynamodb-firestore-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com
    ```
