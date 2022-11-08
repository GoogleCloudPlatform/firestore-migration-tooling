
# Copying data from DynamoDB to Firestore

You can run the script [cp_ddb_firestore.py](./cp_ddb_firestore.py) to copy the records from a DynamoDB table directly to Firestore.

In this document, you run all commands in [Google Cloud Shell]([https://cloud.google.com/shell). You also need admin access (or IAM users with sufficient permissions) for the AWS account and the GCP project.

## Configuring AWS access

1. Install AWS CLI in Cloud Shell.
    ```bash
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    ```
    Note: Since Cloud Shell will not save files except those under your home directly, you may have to reinstall the tool if you have a new Cloud Shell instance.

1. Ensure you have the access key ID and the secret access key for the AWS IAM user you are using. If you don't, you can use [the steps](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-prereqs.html) in the AWS CLI doc to create them. If you don't want to use an admin user, you can use an IAM user with sufficient permissions for DynamoDB.

1.  Configure the AWS Command Line Interface (CLI).

    ```
    aws configure
    ```

1.  The following output appears:
    ```
    $ aws configure 
    AWS Access Key ID [None]: **PASTE_YOUR_ACCESS_KEY_ID**  
    AWS Secret Access Key [None]: **PASTE_YOUR_SECRET_ACCESS_KEY**  
    Default region name [None]: us-east-1  
    Default output format [None]:
     ```

1.  Enter the **ACCESS KEY ID** and **SECRET ACCESS KEY** from the AWS IAM account that you created.
    
    In the **Default region name** field, enter the region you want to use, for example, `us-east-1`. Leave other fields at their default values.

## Configuring Google Cloud access

If you haven't enabled the Firestore API and set it up, you can use the following steps to do it. For more details, you can read the Firestore doc: [Create a Firestore in Native mode database](https://cloud.google.com/firestore/docs/quickstart-servers#create_a_in_native_mode_database).

**Note:** Since Cloud Firestore API is not available for Datastore Mode projects, you have to use Firestore in Native mode. You can switch from Datastore Mode to Native Mode but the change is permanent.

1. Go to the [Firestore console](https://console.cloud.google.com/firestore/data)

1. From the `Select a database service` screen, choose Firestore in Native mode or Firestore in Datastore mode depending on your requirements.

1. Select a [location](https://cloud.google.com/firestore/docs/locations#types) for your Firestore.

   **Warning:** After you set your project's default GCP resource location, you cannot change it.

1. Click Create Database.

## Preparing your environment

1. Clone the GitHub repository containing the code.
    ```
    git clone https://github.com/GoogleCloudPlatform/firestore-migration-tooling.git
    ```

1. Go to the directory.
    ```
    cd firestore-migration-tooling/dynamodb-firestore/copy-data
    ```

1. Create a Python [virtual environment](https://docs.python.org/3/library/venv.html)
    ```
    python3 -mvenv venv
    ```

1. Activate the virtual environment.
    ```
    source venv/bin/activate
    ```

1. Install the required Python modules.
    ```
    pip install -r requirements.txt
    ```

## Copying and viewing the data

1. Run the script to copy the data.

* If you want to copy the data driectly from a DynamoDB to Firestore in native mode, run the following:
    ```
    python ./cp_ddb_firestore.py  [your-dynamodb-table-name]
    ```
* If you want to copy the data driectly from a DynamoDB to Firestore in datastore mode, run the following:
    ```
    python ./cp_ddb_datastore.py  [your-dynamodb-table-name]
    ```
* If you have exported the data to an S3 bucket, run the following command for the native mode:
    ```
    python ./cp_export_firestore.py [table name] [s3 URI]
    ```
    For example:
    ```
    python ./cp_export_firestore.py Customer_Order s3://export-bucket/AWSDynamoDB/01667837262018-1223ed5d/
    ```
* If you have exported the data to an S3 bucket, run the following command for the datastore mode:
    ```
    python ./cp_export_datastore.py [table name] [s3 URI]
    ```
    For example:
    ```
    python ./cp_export_datastore.py Customer_Order s3://export-bucket/AWSDynamoDB/01667837262018-1223ed5d/
    ```

1. View the data in the [Firestore Console](https://console.cloud.google.com/firestore/data)