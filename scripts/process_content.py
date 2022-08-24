"""
Script for extracting relevant data from text that was recognized based on
receipt image.
"""
import re
import os
import json
from pathlib import Path


# Set input file name
content_filename = Path('Paragon_2022-08-11_081131_300dpi.txt')
content_filepath = Path('../results') / content_filename.stem / 'content.txt'

# Set output folder path
out_folderpath = content_filepath.parent


def get_shop(text, str_if_unrecognized='unknown'):
    """Extract shop name from receipt's raw content.

    Return shop name if it exists in receipt text by comparing defined shop
    names with receipt text.

    Args:
        text(str): recognized receipt content
        str_if_unrecognized(str): value to be returned if shop name is not found
            in text (default 'unknown')

    Return:
        str: recognized shop name, str_if_unrecognized value otherwise

    """
    SHOPS = {
        'Biedronka': ('biedronka',),
        'Rossmann': ('rossmann',),
        'Żabka': ('żabka', 'zabka'),
    }

    for row in text:
        for shop, names in SHOPS.items():
            for name in names:
                if name in row.lower():
                    return shop

    return str_if_unrecognized


def get_products(text, write_raw=True, write_processed=True):
    """Return products extracted from text.

    Return a list of products that were recognized in the text. Products
    recognition process is executed using regular expressions.

    Each product is a dictionary with the following attributes:
        - 'name' - product name,
        - 'quantity' - number of pieces or product mass,
        - 'price' - price of a single product,
        - 'total_price' - quantity multiplied by price.

    Optionally, matched text can be saved to text files to help debugging.

    Arguments:
        text (str): input string from which data will be extracted
        write_raw (bool): write matched regex pattern to raw_products.txt
            (default True)
        write_processed (bool): write processed matched items to
            processed_products.txt (default True)

    Returns:
        list: collection (list) of products (dictionaries)
    """
    # Define regex for product data extraction
    product_regex = re.compile(r'''(
            (.+)            # product
            \s+\S{1,2}\s+   # char surrounded with spaces
            (\d([,.]\d+)?)  # quantity
            \s*             # space
            \S{1,2}         # "x"
            (\d+,\s?\d{2})  # product price
            \s+             # space
            (\d+,\s?\d{2})  # total sum for product
        )''', re.VERBOSE)

    products = []
    groups_list = []

    for row in text:
        match = re.search(product_regex, row)
        if match:
            groups = match.groups()
            groups_list.append(groups)

            products.append({
                'name': groups[1],
                'quantity': groups[2],
                'price': groups[4],
                'total_price': groups[5]
            })

    if write_raw:
        raw_products_str = [groups[0] for groups in groups_list]
        products_filename = 'raw_products.txt'
        products_filepath = out_folderpath / products_filename
        with open(products_filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(raw_products_str))
        print(f'Raw products were written to file "{products_filepath}"')

    if write_processed:
        products_str = [f'{groups[1]} {groups[2]} x{groups[4]} {groups[5]}'
                        for groups in groups_list]
        products_filename = 'processed_products.txt'
        products_filepath = out_folderpath / products_filename
        with open(products_filepath, 'w') as f:
            f.write('\n'.join(products_str))
        print(f'Processed products were written to file "{products_filepath}"')

    return products


def get_total(text):
    """Return total sum."""
    total_cost_regex = re.compile(r'SUMA\s+\w+\s+(\d+[,.]\d+)')
    match = re.search(total_cost_regex, ''.join(list(text)))

    return match.group(1)


content = {}

# Read text file
with open(content_filepath, 'r', encoding='utf-8') as f:
    text = f.readlines()
print(f'Text content was read from file "{content_filepath}"')

# Extract shop name
content['shop'] = get_shop(text)

# Replace common wrong characters
text = list(map(lambda x: x.replace('{', '1'), text))
text = list(map(lambda x: x.replace('(', '1'), text))

# Define lists for storing products
content['products'] = get_products(text)

# Extract total cost
content['total_sum'] = get_total(text)

# Write extracted content to json file
json_content_filename = 'content.json'
json_content_filepath = out_folderpath / json_content_filename
with open(json_content_filepath, 'w') as f:
    json.dump(content, f, indent=4)
print(f'Processed content was written to file "{json_content_filepath}"')
