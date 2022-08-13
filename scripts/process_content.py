"""
Script for extracting relevant data from text that was recognized based on
receipt image.
"""
import re
import os
import json
from pathlib import Path

# Set input file path
txt_content_filename = 'Paragon_2022-08-11_081131_300dpi.txt'
txt_content_filepath = Path('../results') / txt_content_filename


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
with open(txt_content_filepath, 'r', encoding='utf-8') as f:
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

# Extract total cost
total_cost_regex = re.compile(r'SUMA\s+\w+\s+(\d+[,.]\d+)')
match = re.search(total_cost_regex, ''.join(list(text)))
content['total_sum'] = match.group(1)

# Define a regex pattern for price
price_regex = r'\d+\.\d+'


with open('res.json', 'w') as f:
    json.dump(content, f, indent=4)