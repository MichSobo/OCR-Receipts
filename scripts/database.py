"""
Code for interacting with MySQL database.
"""
import os

import mysql.connector


def connect(**kwargs):
    """Set a connection to MySQL and return Connection and Cursor objects."""
    try:
        cfg_filepath = kwargs['option_files']
    except KeyError:
        pass
    else:
        abspath = os.path.abspath(cfg_filepath)
        if os.path.isfile(cfg_filepath):
            print(f'\nUsing MySQL configuration file {abspath}')
        else:
            raise FileNotFoundError(
                f'\nMySQL configuration file not found in {abspath}')

    # Connect to MySQL
    try:
        connection = mysql.connector.connect(**kwargs)
    except Exception as e:
        print(e)
        return None, None
    else:
        return connection, connection.cursor(dictionary=True)


def get_item_by_name(cursor, table, name):
    query = f'SELECT * FROM {table} WHERE name = "{name}"'
    cursor.execute(query)

    return cursor.fetchall()


def add_invalid_item_name(cursor, name, valid_name, receipt_id):
    query = f'INSERT INTO invalid_item (name, valid_name, receipt_id) VALUES ("{name}", "{valid_name}", "{receipt_id}")'
    cursor.execute(query)


def add_existing_invalid_item_name(cursor, name):
    # Update invalid name count
    query = f'UPDATE invalid_item SET count = count + 1 WHERE name = "{name}"'
    cursor.execute(query)


def add_valid_item_name(cursor, name):
    query = f'INSERT INTO item VALUES ("{name}");'
    cursor.execute(query)


def add_receipt(cursor,
                image_name, shopping_date, shop_name, total_sum,
                processed_date=None):

    def get_shop_id_by_name(name):
        query = f'SELECT id FROM shop WHERE name = "{name}"'
        cursor.execute(query)

        return cursor.fetchall()[0]['id']


    query_data = {
        'image_name': f'"{image_name}"',
        'shopping_date': f'"{shopping_date}"',
        'shop_id': get_shop_id_by_name(shop_name),
        'total_sum': total_sum
    }

    if processed_date:
        query_data['processed_date'] = processed_date

    columns_str = ', '.join(query_data.keys())
    values_str = ', '.join(map(str, query_data.values()))

    query = f'INSERT INTO receipt ({columns_str}) VALUES ({values_str})'
    cursor.execute(query)

    return cursor.lastrowid


def get_receipts(cursor):
    query = f'SELECT image_name FROM receipt'
    cursor.execute(query)

    result = cursor.fetchall()
    filenames = [row['image_name'] for row in result]

    return filenames


def get_receipts_data(cursor):
    query = f'SELECT id, image_name FROM receipt'
    cursor.execute(query)

    result = cursor.fetchall()

    return result


def get_items_unit_price_history(cursor):
    query = f'SELECT name, shopping_date AS date, unit_price ' \
            f'FROM all_items ' \
            f'INNER JOIN receipt ON all_items.receipt_id = receipt.id ' \
            f'WHERE name in (' \
            f'SELECT name FROM all_items GROUP BY name HAVING count(*) > 1' \
            f') ' \
            f'ORDER BY name, date'
    cursor.execute(query)

    result = cursor.fetchall()

    return result


def add_item(cursor, receipt_id, name, qty, unit_price, total_discount):
    query_data = {
        'receipt_id': receipt_id,
        'name': f'"{name}"',
        'qty': qty,
        'unit_price': unit_price,
        'total_discount': total_discount
    }

    columns_str = ', '.join(query_data.keys())
    values_str = ', '.join(map(str, query_data.values()))

    query = f'INSERT INTO all_items ({columns_str}) VALUES ({values_str})'
    cursor.execute(query)
