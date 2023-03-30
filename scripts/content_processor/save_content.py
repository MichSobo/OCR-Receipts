# -*- coding: utf-8 -*-
"""
Code for saving content in a database.
"""
import json
import os

import pandas as pd

from scripts import database


def read_content(path):
    """Read a file with processed content and return it as a dictionary.

    Arguments:
        path (str): path to the file with processed content

    Returns:
        dict: dictionary with file content

    """
    with open(path, encoding='utf-8') as f:
        content = json.load(f)

    print(f'Using content from file "{os.path.abspath(path)}"')

    return content


def get_valid_name(cursor, item):
    if database.get_item_by_name(cursor, 'item', item['name']):
        # If item name exists in db as valid name, use it
        print(f'Found "{item["name"]}" in database as valid name')
        valid_name = item['name']
    elif database.get_item_by_name(cursor, 'invalid_item', item['name']):
        # If item name exists in db as invalid name, increase counter...
        print(f'Found "{item["name"]}" in database as invalid name')
        database.add_existing_invalid_item_name(cursor, item['name'])

        # ... and get corresponding valid name
        valid_name = database.get_item_by_name(cursor,
                                               'invalid_item',
                                               item['name'])[0]['valid_name']
        print(f'Using "{valid_name}" instead')
    else:
        # If item name not exists in db, add it to both tables
        print(f'Item name was not found in database')

        # Get valid name from user input
        user_input = input('Enter valid name or press Enter to skip: ')

        valid_name = user_input if user_input != '' else item['name']

        if not database.get_item_by_name(cursor, 'item', valid_name):
            # If valid name not exists in db, add it
            print(f'Adding valid name "{valid_name}" to database')
            database.add_valid_item_name(cursor, valid_name)

        if user_input != '':
            # Add invalid item name to db
            print(f'Adding invalid name "{item["name"]}" to database')
            database.add_invalid_item_name(cursor, item['name'], valid_name, receipt_id)

    return valid_name


def is_unit_price_valid(df):
    """Return False if unambiguous unit price exists otherwise return True."""
    def is_unique(s):
        return True if len(s.unique()) == 1 else False

    r = df.groupby('name')['unit_price'].apply(is_unique)

    if r.all():
        return True
    else:
        print('Unambiguous unit price was found for items: ', end='')
        print(', '.join(r.loc[r == False].index.values))

        return False


def save_content_in_db(content, connection=None, cursor=None):
    if connection is None or cursor is None:
        # Connect to database
        connection, cursor = database.connect(option_files='..\\..\\my.ini',
                                              database='shopping')

    # Get content
    if isinstance(content, dict):
        pass
    elif isinstance(content, str):
        # Read content from file
        if os.path.isfile(content):
            content = read_content(content)
        else:
            raise ValueError(f'Path to content "{content}" does not exist')
    else:
        raise TypeError(
            f'Unsupported argument type passed as content: {type(content)}')

    # Get image name
    image_filename = os.path.basename(content['image_filepath'])

    # Add receipt data to db
    global receipt_id
    receipt_id = database.add_receipt(cursor,
                                      image_filename, content['shopping_date'],
                                      content['shop_name'], content['total_sum'])

    # Set valid item names
    print(f'\n{"=" * 20}\nSETTING VALID NAMES\n{"=" * 20}')
    for item in content['items']:
        # Update item name
        print(f'''\nSetting name for item identified as "{item["name"]}"''')
        item['name'] = get_valid_name(cursor, item)

    print('\nAll item names have been set')

    # Set DataFrame with items
    df = pd.DataFrame(content['items'])

    # Check for unambiguous unit price for the same item name
    if not is_unit_price_valid(df):
        raise ValueError(f'Unambiguous unit prices were found')

    # Group item data by name to remove duplicates and sum properties
    df_grouped = df.groupby('name',
                            as_index=False,
                            sort=False)[['qty', 'total_discount']].sum(numeric_only=False)

    # Merge grouped data with unit prices
    final_df = pd.merge(df_grouped, df[['name', 'unit_price']],
                        how='inner',
                        on='name').drop_duplicates('name', ignore_index=True)

    # Add items to db
    for index, row in final_df.iterrows():
        database.add_item(cursor,
                          receipt_id=receipt_id,
                          name=row['name'],
                          qty=row['qty'],
                          unit_price=row['unit_price'],
                          total_discount=row['total_discount'])

    connection.commit()

    if connection is None or cursor is None:
        cursor.close()
        connection.close()


def main():
    # Set paths
    ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..'))

    content_folderpath = os.path.join(ROOT_FOLDERPATH, 'results',
                                      'Paragon_2023-03-26_231157')

    # Read processed extracted content
    content_filename = 'processed_content.json'
    content_filepath = os.path.join(content_folderpath, content_filename)

    save_content_in_db(content_filepath)


if __name__ == '__main__':
    main()
