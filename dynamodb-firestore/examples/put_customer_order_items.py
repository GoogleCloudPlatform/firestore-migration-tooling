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

from decimal import Decimal
import boto3
import csv

dynamo = boto3.resource('dynamodb')


def put_customer_item(pk, sk, customer_id, customer_fname, customer_lname, customer_email, customer_addresses):

    table = dynamo.Table('Customer_Order')
    resp = table.put_item(
        Item={
            'PK': pk,
            'SK': sk,
            'customer_id': customer_id,
            'customer_fname': customer_fname,
            'customer_lname': customer_lname,
            'customer_email': customer_email,
            'customer_addresses': customer_addresses
        }
    )

    return resp


def process_customer_items():

    with open('sample_data/customer.tsv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(reader)  # skip header line

        for row in reader:

            #print('row: ' + str(row))

            pk = row[0]
            sk = row[1]
            customer_id = row[2]
            customer_fname = row[3]
            customer_lname = row[4]
            customer_email = row[5]
            customer_addresses = row[6]

            print('pk: ' + pk)
            print('sk: ' + sk)
            print('customer_id: ' + customer_id)
            print('customer_fname: ' + customer_fname)
            print('customer_lname: ' + customer_lname)
            print('customer_email: ' + customer_email)
            print('customer_addresses: ' + customer_addresses)

            resp = put_customer_item(
                pk, sk, customer_id, customer_fname, customer_lname, customer_email, customer_addresses)

            print('resp: ' + str(resp))


def put_order_item(pk, sk, customer_id, order_id, order_status, order_ts, order_amount, number_of_items):

    table = dynamo.Table('Customer_Order')
    resp = table.put_item(
        Item={
            'PK': pk,
            'SK': sk,
            'customer_id': customer_id,
            'order_id': order_id,
            'order_status': order_status,
            'order_ts': order_ts,
            'order_amount': order_amount,
            'number_of_items': number_of_items
        }
    )

    return resp


def process_order_items():

    with open('sample_data/order.tsv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(reader)  # skip header line

        for row in reader:

            #print('row: ' + str(row))

            pk = row[0]
            sk = row[1]
            customer_id = row[2]
            order_id = row[3]
            order_status = row[4]
            order_ts = row[5]
            order_amount = Decimal(row[6])
            number_of_items = int(row[7])

            print('pk: ' + pk)
            print('sk: ' + sk)
            print('customer_id: ' + customer_id)
            print('order_id: ' + order_id)
            print('order_status: ' + order_status)
            print('order_ts: ' + order_ts)
            print('order_amount: ' + str(order_amount))
            print('number_of_items: ' + str(number_of_items))

            resp = put_order_item(pk, sk, customer_id, order_id,
                                  order_status, order_ts, order_amount, number_of_items)

            print('resp: ' + str(resp))


def put_line_item(pk, sk, order_id, line_item_id, product_id, item_price, item_discount, item_quantity, item_status, comment):

    table = dynamo.Table('Customer_Order')
    resp = table.put_item(
        Item={
            'PK': pk,
            'SK': sk,
            'order_id': order_id,
            'line_item_id': line_item_id,
            'product_id': product_id,
            'item_price': item_price,
            'item_discount': item_discount,
            'item_quantity': item_quantity,
            'item_status': item_status,
            'comment': comment
        }
    )

    return resp


def process_line_items():

    with open('sample_data/line_item.tsv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(reader)  # skip header line

        for row in reader:

            #print('row: ' + str(row) + ', len: ' + str(len(row)))

            pk = row[0]
            sk = row[1]
            order_id = row[2]
            line_item_id = row[3]
            product_id = row[4]
            item_price = Decimal(row[5])
            item_discount = Decimal(row[6])
            item_quantity = int(row[7])
            item_status = row[8]

            if len(row) > 9:
                comment = row[9]
            else:
                comment = None

            print('pk: ' + pk)
            print('sk: ' + sk)
            print('order_id: ' + order_id)
            print('line_item_id: ' + line_item_id)
            print('product_id: ' + product_id)
            print('item_price: ' + str(item_price))
            print('item_discount: ' + str(item_discount))
            print('item_quantity: ' + str(item_quantity))
            print('item_status: ' + item_status)

            if comment is not None:
                print('comment: ' + comment)

            resp = put_line_item(pk, sk, order_id, line_item_id, product_id,
                                 item_price, item_discount, item_quantity, item_status, comment)

            print('resp: ' + str(resp))


if __name__ == '__main__':
    process_customer_items()
    process_order_items()
    process_line_items()
