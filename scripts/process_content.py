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


content = {}

# Read text file
with open(content_filepath, 'r', encoding='utf-8') as f:
    text = f.readlines()
print(f'Text content was read from file "{content_filepath}"')

# Extract shop name
content['shop'] = get_shop(text)

# Define regex for data extraction
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

# Replace common wrong characters
text = list(map(lambda x: x.replace('{', '1'), text))
text = list(map(lambda x: x.replace('(', '1'), text))
content['products'] = []

# Define lists for storing products
raw_products = []
products = []

# Extract all products with quantity and prices
for row in text:
    match = re.search(product_regex, row)
    if match:
        groups = match.groups()

        content['products'].append({
            'name': groups[1],
            'quantity': groups[2],
            'price': groups[4],
            'total_price': groups[5]
        })

        raw_products.append(groups[0])

        products.append(
            " ".join([groups[1], groups[2], 'x' + groups[4], groups[5]])
        )

# Write raw products to text file
products_filename = 'raw_products.txt'
products_filepath = out_folderpath / products_filename
with open(products_filepath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(raw_products))
print(f'Raw products were written to file "{products_filepath}"')

# Write products to text file
products_filename = 'products.txt'
products_filepath = out_folderpath / products_filename
with open(products_filepath, 'w') as f:
    f.write('\n'.join(products))
print(f'Processed products were written to file "{products_filepath}"')

# Extract total cost
total_cost_regex = re.compile(r'SUMA\s+\w+\s+(\d+[,.]\d+)')
match = re.search(total_cost_regex, ''.join(list(text)))
content['total_sum'] = match.group(1)

# Write extracted content to json file
json_content_filename = 'content.json'
json_content_filepath = out_folderpath / json_content_filename
with open(json_content_filepath, 'w') as f:
    json.dump(content, f, indent=4)
print(f'Processed content was written to file "{json_content_filepath}"')
