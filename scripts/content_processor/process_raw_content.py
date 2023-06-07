"""
Code for extracting relevant data from recognized receipt content.
"""
import json
import os
import re

import pyinputplus as pyip

from scripts.content_processor.misc import string_to_float


def read_raw_content(path):
    """Read a file with raw content and return it as a string.

    Arguments:
        path (str): path to the file with raw content

    Returns:
        str: file content as a string

    """
    with open(path, encoding='utf-8') as f:
        raw_content = f.read()

    abspath = os.path.abspath(path)
    print(f'Raw content was read from file "{abspath}"')

    return raw_content


def replace_invalid_chars(text):
    """Replace invalid characters in text and return new text.

    Arguments:
        text (str): input text

    Returns:
        str: text with replaced characters
    """
    # Define mapper where key-correct -> value-wrong
    mapper = {
        '1': ['(', '{'],
        'x': ['«', '¥', '#'],
        '-': ['~'],
        'P': ['?']
    }

    new_text = text

    for valid, invalid in mapper.items():
        for char in invalid:
            new_text = new_text.replace(char, valid)

    return new_text


def get_split_text(text):
    """Split text by new line character and return it as a list.

    The target of the function is to get a list of rows that takes into account
    the fact that a row may refer to a discounted product.

    To detect such products, it is checked whether "OPUST" word is present in
    current row. If so, the preceding row will be extended with the current row
    and the following row. Otherwise, a single-element list consisting of the
    current row will be added to a list.

    Arguments:
        text (str): input text

    Returns:
        list: row-separated text, including discounted products

    """
    # """Return a split text by new lines, considering discount."""
    text_split = text.split('\n')

    # Remove empty lines
    text_split = list(filter(lambda x: x != '', text_split))

    # Consider discount
    text_split_new = []

    i = 0
    while i < len(text_split):
        line = text_split[i]

        if 'OPUST' in line:
            text_split_new[-1] += [line, text_split[i + 1]]
            i += 2
        else:
            text_split_new.append([line])
            i += 1

    return text_split_new


def get_shop_name(text, do_correct=True, value_if_not_recognized=None):
    """Return shop name if found in receipt content.

    The function tries to extract shop name by comparing defined shop names with
    receipt content. If matching word found, a shop name will be returned.

    In case of no match and *do_correct* argument set to True, user will be
    asked to enter a correct name. Otherwise, *str_if_not_recognized* argument
    value will be returned.

    Arguments:
        text (str): input text
        do_correct (bool): set whether to ask user for correct values
            (default True)
        value_if_not_recognized (str): value to be returned if shop name not
            found in text (default None)

    Returns:
        str: recognized shop name, *value_if_not_recognized* otherwise

    """
    SHOPS = {
        'Biedronka': ('biedronka',),
        'Rossmann': ('rossmann',),
        'Żabka': ('żabka', 'zabka'),
    }

    for name, possible_names in SHOPS.items():
        for possible_name in possible_names:
            if possible_name in text.lower():
                return name

    # In case shop name not recognized
    if do_correct:
        value = input('\nShop name was not recognized. Enter correct value: ')
        return get_shop_name(value)
    else:
        return value_if_not_recognized


def get_qty(string):
    """Return quantity string in proper format based on another string."""
    pattern = re.compile(r'(\d+)([,. ]+(\d{,3}))?')
    match = pattern.match(string).groups()

    if match[2] is None:
        # If qty is an integer, return the first match group
        return match[0]
    else:
        # If qty is float, return both groups
        return f'{match[0]}.{match[2]}'


def get_price(string, is_discount=False):
    """Return price string in proper format based on another string.

    The function can also process strings that represent discount. For that it
    uses a different regex pattern.

    Arguments:
        string (str): input string
        is_discount (bool): set whether the string represents a discount
            (default False)

    Returns:
        str: price string

    """
    discount_pattern = re.compile(r'OPUST.*(\w+)[,. ]+(\w{,2})')
    price_pattern = re.compile(r'(\w+)[,. ]+(\w{,2})')

    pattern = discount_pattern if is_discount else price_pattern
    match = pattern.search(string).groups()

    return f'{match[0]}.{match[1]}'


def get_shopping_date(text, do_correct=True, value_if_not_recognized=None):
    """Get shopping date and return it.

    Shopping date will be extracted from text. If it's not found, user will be
    asked to enter the date if *do_correct* argument True, otherwise the
    function will return *value_if_not_recognized*.

    Arguments:
        text (str): text for shopping date extraction,
        do_correct (bool): set whether to interactively correct invalid values
            (default True)
        value_if_not_recognized (object): value to be returned if shopping date
            not found in text (default None)

    Returns:
        str: shopping date

    """

    def get_date():
        while True:
            date = input('\nEnter correct date in format yyyy-mm-dd: ')

            if pattern.fullmatch(date):
                return date
            else:
                print('Incorrect date format')

    pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    match = pattern.search(text)

    if match:
        date = match.group()
        print(f'\nRecognized shopping date is: {date}')

        if pyip.inputYesNo('Is it correct? ') == 'yes':
            return date
        else:
            return get_date()
    else:
        print('\nShopping date was not recognized')

        if do_correct:
            return get_date()
        else:
            return value_if_not_recognized


def get_item(text, do_correct=True):
    """Get item properties from text and return it as a dictionary.

    Arguments:
        text (str): text for item properties extraction
        do_correct (bool): set whether to interactively correct invalid values
            (default True)

    Returns:
        dict: dictionary with item properties

    """
    pattern = re.compile(r'''
        (.+)                    # item name
        \s+\S{1,2}\s+           # char surrounded with spaces
        (\d+([,. ]\d+)?)        # quantity
        \sx?                    # "x"
        ([t\d]+[,.]\s?\d{,2})   # item unit price
        \s+                     # space
        (\d+[,.]\s?\d{,2})      # item total price
    ''', re.VERBOSE)

    result = pattern.match(text)
    if result is None:
        return None

    # Set item properties
    item = {
        'name': result.group(1),
        'qty': get_qty(result.group(2)),
        'unit_price': get_price(result.group(4)),
        'total_price': get_price(result.group(5)),
        'total_discount': 0.0,
        'final_price': None
    }

    # Convert properties from string to numeric
    for key in ('qty', 'unit_price', 'total_price'):
        value = string_to_float(item[key], text, do_correct)
        item[key] = value

    # Set final price as total price
    item['final_price'] = item['total_price']

    return item


def get_items(text, do_correct=True):
    """Return a list of shop items extracted from text.

    Each item is a dictionary with the following attributes:
        - 'name' - item name,
        - 'qty' - item quantity,
        - 'unit_price' - item unit price,
        - 'total_price' - item total price.

    Optionally, matched text can be saved to text files to help debugging.

    Arguments:
        text (str): input string from which data will be extracted
        do_correct (bool): set whether to interactively correct invalid values
            (default True)

    Returns:
        list[dict]: list of items
    """
    # Get split text (for each item, including discount)
    split_text = get_split_text(text)

    items = []
    for line in split_text:
        item_line = line[0]

        # Get item properties
        item = get_item(item_line, do_correct)
        if item is None:
            continue

        if len(line) > 1:
            # Modify discount and final price properties
            discount_line, final_price_line = line[1], line[2]
            discount = get_price(discount_line, is_discount=True)
            final_price = get_price(final_price_line)

            # Update properties
            item['total_discount'] = string_to_float(discount, item_line, do_correct)
            item['final_price'] = string_to_float(final_price, item_line, do_correct)

        # Add item to list of items
        items.append(item)

    return items


def get_total_sum(text, do_correct=True, value_if_not_recognized=None):
    """Return total shopping sum.

    Arguments:
        text (str): input string for total sum extraction
        do_correct (bool): set whether to interactively correct invalid values
            (default True)
        value_if_not_recognized (float): value to be returned if shop name is
            not found in the text (default None)

    Returns:
        float: recognized total sum, *value_if_not_recognized* otherwise

    """
    pattern = re.compile(r'SUMA PLN (\d+[,. ]+\d{2})')
    match = pattern.search(text)

    if match:
        price_str = get_price(match.group(1))
        return string_to_float(price_str)
    else:
        if do_correct:
            prompt = '\nTotal sum was not recognized. Enter correct value: '
            value = input(prompt)

            return string_to_float(value)
        else:
            return value_if_not_recognized


def extract_content(input_filepath,
                    img_content=None,
                    do_correct=True,
                    do_save=True,
                    output_folderpath=''):
    """Extract content from raw text and return it as a dictionary.

    The extracted content items are put in a dictionary as:
    - 'content_filepath' - path to the file that was used as a source for
        content extraction,
    - 'shop_name' - name of the shop,
    - 'items' - shop items on the receipt,
    - 'total_sum' - total sum on the receipt.

    Arguments:
        input_filepath (str): path to a text file with recognized image content
        img_content (str): recognized image content (default None)
        do_correct (bool): set whether to ask user for correct values
            (default True)
        do_save (bool): set whether to save the extracted content to a JSON file
            (default True)
        output_folderpath (str): path to the output folder (default '')

    Return:
        dict: dictionary with extracted content

    """
    # Read raw content
    raw_content = img_content if img_content else read_raw_content(input_filepath)

    # Replace common wrong characters
    content = replace_invalid_chars(raw_content)

    # Get shopping date
    shopping_date = get_shopping_date(content, do_correct=do_correct)

    # Get shop name
    shop_name = get_shop_name(raw_content, do_correct=do_correct)

    # Get items
    items = get_items(content, do_correct=do_correct)

    # Get total sum
    total_sum = get_total_sum(raw_content, do_correct=do_correct)

    # Set result dictionary
    extracted_content = {
        'image_filepath':   os.path.abspath(input_filepath),
        'shopping_date':    shopping_date,
        'shop_name':        shop_name,
        'items':            items,
        'total_sum':        total_sum
    }

    if do_save is True:
        # Write recognized content to file
        output_filepath = os.path.join(output_folderpath, 'extracted_content.json')
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(extracted_content, f, ensure_ascii=False, indent=4)

        abspath = os.path.abspath(output_filepath)
        print(f'\nExtracted content was written to file "{abspath}"')

    return extracted_content


def main():
    # Set default paths
    ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..'))

    content_folderpath = os.path.join('results',
                                      'Paragon_2022-08-11_081131_300dpi')

    # Set path to raw content
    content_filename = 'raw_content.txt'
    content_filepath = os.path.join(ROOT_FOLDERPATH,
                                    content_folderpath, content_filename)

    # Get extracted content
    output_folderpath = os.path.join(ROOT_FOLDERPATH, content_folderpath)

    extract_content(content_filepath,
                    output_folderpath=output_folderpath)


if __name__ == '__main__':
    main()
