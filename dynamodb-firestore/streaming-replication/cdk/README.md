
# Using AWS CDK to configure and deploy the Lambda function

In this doc, we use [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html) to deploy and manage the AWS resources.

1. If you haven't installed the [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html), use the following command to install it:

    ```bash
    sudo npm install -g aws-cdk
    ```
    
1. Set up the variables.

    ```bash
    export AWS_REGION=us-east-1
    export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    export DYNAMODB_TABLE=[Your DynamoDB table name]
    export GCP_PROJECT_ID=[Your GCP Project ID]
    export APP_NAME=ddb-firestore-sync-app
    export AWS_SECRET_NAME=ddb2firestore/gcp-sa-key
    # change the src location for Firestore datastore mode to ../lambda-func-datastore
    export LAMBDA_SRC_LOCATION=../lambda-func-firestore
    ```

1. Create a service account on GCP and download the key file.

    ```bash
    gcloud iam service-accounts create dynamodb-firestore-sa \
        --description="SA used to copy records from AWS to GCP" \
        --display-name="dynamodb-firestore-sa"

    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:dynamodb-firestore-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/datastore.owner"

    gcloud iam service-accounts keys create gcp-key.json \
        --iam-account=dynamodb-firestore-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com
    ```

1. Create a secret in AWS secrets manager for the GCP service account key file:

    ```bash
    aws secretsmanager create-secret --name $AWS_SECRET_NAME \
    --description "Access GCP firestore" --secret-string $(base64 gcp-key.json)
    ```

1. Get the secret ARN.

    ```bash
    export SECRET_ARN=$(aws secretsmanager describe-secret --secret-id $AWS_SECRET_NAME --query 'ARN' | tr -d '"')
    ```
1. Create a virtualenv:

    ```bash
    python3 -m venv venv
    ```

1. After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

    ```bash
    source venv/bin/activate
    ```

1. Once the virtualenv is activated, you can install the required dependencies.

    ```bash
    pip install -r requirements.txt
    ```

1. If it's the first time you use CDK for the AWS account, you need to use bootstrap to initialize CDK.

    ```bash
    cdk bootstrap
    ```

1. At this point, you can now synthesize the CloudFormation template for this code.

    ```bash
    cdk synth
    ```

1. Deploy the change.

    ```bash
    cdk deploy
    ```
