"""
Script for extracting relevant data from text that was recognized based on
receipt image.
"""
import re
import os
import json
from pathlib import Path

# Set input file path
content_filename = Path('Paragon_2022-08-11_081131_300dpi.txt')
content_filepath = Path('../results') / content_filename.stem / content_filename


def get_shop(text):
    """Extract shop name from receipt text."""
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


content = {}

# Read text file content
with open(content_filepath, 'r', encoding='utf-8') as f:
    text = f.readlines()

# Extract shop name
content['shop'] = get_shop(text)

# Extract all products with quantity and prices
product_regex = re.compile(r'''(
    (.+)            # product
    \s+\S{1,2}\s+   # char surrounded with spaces
    (\d([,.]\d+)?)  # quantity
    \s*             # 0 or more spaces
    [xX]            # "x"
    (\d+[,.]\d{2})  # product price
    \s+             # space
    (\d+[,.]\d{2})  # total sum for product
)''', re.VERBOSE)

# Replace wrong character
text = list(map(lambda x: x.replace('{', '1'), text))
content['products'] = []

products = []

for row in text:
    match = re.search(product_regex, row)
    if match:
        groups = match.groups()
        products.append(groups[0])
        content['products'].append({
            'name': groups[1],
            'quantity': groups[2],
            'price': groups[4],
            'total_price': groups[5]
        })

products_filename = 'products.txt'
products_filepath = content_filepath.parent / products_filename
with open(products_filepath, 'w') as f:
    f.write('\n'.join(products))

# Extract total cost
total_cost_regex = re.compile(r'SUMA\s+\w+\s+(\d+[,.]\d+)')
match = re.search(total_cost_regex, ''.join(list(text)))
content['total_sum'] = match.group(1)

# Define a regex pattern for price
price_regex = r'\d+\.\d+'

with open('res.json', 'w') as f:
    json.dump(content, f, indent=4)

# TODO: Write all extracted products to file (content.txt)
# TODO: Write all extracted products to file (content.json)
# TODO: Build test suite to enhance the extraction process
# TODO: Check that qty * product price = total for product
# TODO: Check that all products - discounts = total sum
# 1 is wrongly taken as 4
# 1 is wrongly taken as {
