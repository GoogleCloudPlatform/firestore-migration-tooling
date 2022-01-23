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

from decimal import Decimal
import boto3
import csv

dynamo = boto3.resource('dynamodb')


def put_book_product_item(pk, sk, product_id, product_category, isbn, book_title, book_authors, book_format, book_publisher, publication_date, price, shipping_amount):

    table = dynamo.Table('Product')
    resp = table.put_item(
        Item={
            'PK': pk,
            'SK': sk,
            'product_id': product_id,
            'product_category': product_category,
            'isbn': isbn,
            'book_title': book_title,
            'book_authors': book_authors,
            'book_format': book_format,
            'book_publisher': book_publisher,
            'publication_date': publication_date,
            'price': price,
            'shipping_amount': shipping_amount
        }
    )

    return resp


def process_book_product_items():

    with open('sample_data/book_product.tsv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(reader)  # skip header line

        for row in reader:

            #print('row: ' + str(row))

            pk = row[0]
            sk = row[1]
            product_id = row[2]
            product_category = row[3]
            isbn = row[4]
            book_title = row[5]
            book_authors = row[6]
            book_format = row[7]
            book_publisher = row[8]
            publication_date = row[9]
            price = Decimal(row[10])
            shipping_amount = Decimal(row[11])

            print('pk: ' + pk)
            print('sk: ' + sk)
            print('product_id: ' + product_id)
            print('product_category: ' + product_category)
            print('isbn: ' + isbn)
            print('book_title: ' + book_title)
            print('book_authors: ' + book_authors)
            print('book_format: ' + book_format)
            print('book_publisher: ' + book_publisher)
            print('publication_date: ' + publication_date)
            print('price: ' + str(price))
            print('shipping_amount: ' + str(shipping_amount))

            resp = put_book_product_item(pk, sk, product_id, product_category, isbn, book_title, book_authors, book_format, book_publisher, publication_date,
                                         price, shipping_amount)

            print('resp: ' + str(resp))


def put_electronic_product_item(pk, sk, product_id, product_name, product_category, price, upc, shipping_amount, product_description, manufacturer, model):

    table = dynamo.Table('Product')
    resp = table.put_item(
        Item={
            'PK': pk,
            'SK': sk,
            'product_id': product_id,
            'product_category': product_category,
            'price': price,
            'upc': upc,
            'shipping_amount': shipping_amount,
            'product_description': product_description,
            'manufacturer': manufacturer,
            'model': model
        }
    )

    return resp


def process_electronic_product_items():

    with open('sample_data/electronic_product.tsv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(reader)  # skip header line

        for row in reader:

            print('row: ' + str(row))

            pk = row[0]
            sk = row[1]
            product_id = row[2]
            product_name = row[3]
            product_category = row[4]
            price = Decimal(row[5])
            upc = row[6]
            shipping_amount = Decimal(row[7])
            product_description = row[8]
            manufacturer = row[9]
            model = row[10]

            print('pk: ' + pk)
            print('sk: ' + sk)
            print('product_id: ' + product_id)
            print('product_name: ' + product_name)
            print('product_category: ' + product_category)
            print('price: ' + str(price))
            print('upc: ' + upc)
            print('shipping_amount: ' + str(shipping_amount))
            print('product_description: ' + product_description)
            print('manufacturer: ' + manufacturer)
            print('model: ' + model)

            resp = put_electronic_product_item(pk, sk, product_id, product_name, product_category, price, upc, shipping_amount, product_description, manufacturer,
                                               model)

            print('resp: ' + str(resp))


if __name__ == '__main__':
    process_book_product_items()
    process_electronic_product_items()
