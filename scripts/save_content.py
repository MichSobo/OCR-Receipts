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
    with open(path) as f:
        content = json.load(f)

    print(f'Processed content was read from file "{os.path.abspath(path)}"')

    return content


def main():
    # Connect to database
    connection, cursor = database.connect(option_files='..\\my.ini',
                                          database='shopping')

    # Set paths
    ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), './..'))

    content_folderpath = os.path.join(ROOT_FOLDERPATH, 'results',
                                      'Paragon_2022-08-11_081131_300dpi')

    # Read processed extracted content
    content_filename = 'processed_extracted_content.json'
    content_filepath = os.path.join(content_folderpath, content_filename)
    content = read_content(content_filepath)

    # Add receipt data
    receipt_id = database.add_receipt(cursor,
                                      image_name='Paragon_2022-08-11_081131_300dpi.jpg',
                                      shop_name=content['shop_name'],
                                      total_sum=content['total_sum'])
    i = 0
    # Get items
    items = content['items']
    for item in items:
        # Check if the name is in db
        if database.get_item_by_name(cursor, 'item', item['name']):
            # If exists as valid, continue
            valid_name = item['name']
        elif database.get_item_by_name(cursor, 'invalid_item', item['name']):
            # If exists as invalid, count+1 and get valid name
            database.add_existing_invalid_item_name(cursor, item['name'])
            valid_name = database.get_item_by_name(cursor,
                                                   'invalid_name',
                                                   item['name'])['valid_name']

        else:
            # Get valid name from user input
            prompt = f'''Set valid name for item recognized as "{item['name']}": '''
            user_input = input(prompt)
            valid_name = user_input if user_input != '' else item['name']

            # Check if valid name is in db
            if not database.get_item_by_name(cursor, 'item', valid_name):
                # If not, add valid name to db
                database.add_valid_item_name(cursor, valid_name)

            # Add invalid name to db
            database.add_invalid_item_name(cursor, item['name'], valid_name)

        # Update item name
        item['name'] = valid_name

        i += 1
        if i == 5:
            break

    df = pd.DataFrame(items)
    df_grouped = df.groupby('name', as_index=False, sort=False).sum(numeric_only=False)

    i = 0
    for index, row in df_grouped.iterrows():
        database.add_item(cursor,
                          receipt_id=receipt_id,
                          name=row['name'],
                          qty=row['qty'],
                          unit_price=row['unit_price'],
                          total_discount=row['total_discount'])
        i += 1
        if i == 5:
            break

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == '__main__':
    main()