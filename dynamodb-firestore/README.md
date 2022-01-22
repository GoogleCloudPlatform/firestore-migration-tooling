
# Migrating from DynamoDB to Firestore

The approach described here for migrating from Amazon DynamoDB to Google Firestore has two parts.

-  First, you will enable streaming for the DynamoDB table you want to migrate. After that, you will deploy a Lambda function triggered by the changes(add/update/delete) captured in the stream. The Lambda function will replicate those changes to a Firestore database near real-time. Please read [streaming-replication/README.md](./streaming-replication/README.md) for more details.

- In the second part, you will run a script that directly copies the records from DynamoDB to the Firestore database you specified. Please read [copy-data/README.md](./copy-data/README.md) for more details.

Those two steps can be used independently. However, you can minimize the impact to your users for the migration by combining both of them.
