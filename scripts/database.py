"""Code for interacting with MySQL database."""
import os
import pprint

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
    query = f'SELECT * FROM {table} WHERE name = "{name}";'
    cursor.execute(query)

    return cursor.fetchall()


def add_invalid_item_name(cursor, name, valid_name):
    query = f'INSERT INTO invalid_item (name, valid_name) VALUES ("{name}", "{valid_name}")'
    cursor.execute(query)


def add_existing_invalid_item_name(cursor, name):
    # Update invalid name count
    query = f'UPDATE invalid_item SET count = count + 1 WHERE name = {name}'
    cursor.execute(query)


def add_valid_item_name(cursor, name):
    query = f'INSERT INTO item VALUES ("{name}");'
    cursor.execute(query)


def add_receipt(cursor,
                image_name, shop_name, total_sum,
                processed_date=None, shopping_date=None):

    def get_shop_id_by_name(name):
        query = f'SELECT id FROM shop WHERE name = "{name}"'
        cursor.execute(query)

        return cursor.fetchall()[0]['id']


    query_data = {
        'image_name': f'"{image_name}"',
        'shop_id': get_shop_id_by_name(shop_name),
        'total_sum': total_sum
    }

    if processed_date:
        query_data['processed_date'] = processed_date

    if shopping_date:
        query_data['shopping_date'] = shopping_date

    columns_str = ', '.join(query_data.keys())
    values_str = ', '.join(map(str, query_data.values()))

    query = f'INSERT INTO receipt ({columns_str}) VALUES ({values_str})'
    cursor.execute(query)

    return cursor.lastrowid


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


if __name__ == '__main__':
    printer = pprint.PrettyPrinter(indent=1)

    cnx, cursor = connect(option_files='..\\my.ini', database='shopping', use_pure=True)


    cursor.close()
    cnx.close()
