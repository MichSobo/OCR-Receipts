"""
Script for extracting relevant data from recognized receipt content.
"""
import json
import os
import re

from scripts.content_detector.misc import string_to_float


def read_raw_content(filepath):
    """Read a file with raw content and return it as a string.

    Arguments:
        filepath (str): path to the file with raw content

    Returns:
        str: file content as a string

    """
    with open(filepath, encoding='utf-8') as f:
        raw_content = f.read()

    path = os.path.abspath(filepath)
    print(f'Raw content was read from file "{path}"')

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
        'x': ['«', '¥'],
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


def get_shop_name(text, do_correct=True, value_if_not_recognized=False):
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
            found in text (default False)

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

    # In case shop name was not recognized
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
    discount_pattern = re.compile(r'OPUST -?(\w+)[,. ]+(\w{,2})')
    price_pattern = re.compile(r'(\w+)[,. ]+(\w{,2})')

    pattern = discount_pattern if is_discount else price_pattern
    match = pattern.search(string).groups()

    return f'{match[0]}.{match[1]}'


def get_item(text, log=True, do_correct=True):
    """Get item properties from text and return it as a dictionary.

    Arguments:
        text (str): text for item properties extraction
        log (bool): set whether to print log messages (default True)
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
        'total_discount': None,
        'final_price': None
    }

    # Convert properties from string to numeric
    for key in ('qty', 'unit_price', 'total_price'):
        value = string_to_float(item[key], log, text, do_correct)
        item[key] = value

    # Set final price as total price
    item['final_price'] = item['total_price']

    return item


def get_items(text, log=True, do_correct=True):
    """Return a list of shop items extracted from text.

    Each item is a dictionary with the following attributes:
        - 'name' - item name,
        - 'qty' - item quantity,
        - 'unit_price' - item unit price,
        - 'total_price' - item total price.

    Optionally, matched text can be saved to text files to help debugging.

    Arguments:
        text (str): input string from which data will be extracted
        log (bool): set whether to print log messages (default True)
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
        item = get_item(item_line, log, do_correct)
        if item is None:
            continue

        if len(line) > 1:
            # Modify discount and final price properties
            discount_line, final_price_line = line[1], line[2]
            discount = get_price(discount_line, is_discount=True)
            final_price = get_price(final_price_line)

            # Update properties
            item['total_discount'] = string_to_float(discount, log, item_line, do_correct)
            item['final_price'] = string_to_float(final_price, log, item_line, do_correct)

        # Add item to list of items
        items.append(item)

    return items


def get_total_sum(text, do_correct=True, value_if_not_recognized=False):
    """Return total shopping sum.

    Arguments:
        text (str): input string for total sum extraction
        do_correct (bool): set whether to interactively correct invalid values
            (default True)
        value_if_not_recognized (float): value to be returned if shop name is
            not found in the text (default False)

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
                    log=True,
                    do_correct=True,
                    do_save=True,
                    output_filepath='extracted_content.json'):
    """Extract content from raw text and return it as a dictionary.

    The extracted content items are put in a dictionary as:
    - 'content_filepath' - path to the file that was used as a source for
        content extraction,
    - 'shop_name' - name of the shop,
    - 'items' - shop items on the receipt,
    - 'total_sum' - total sum on the receipt.

    Arguments:
        input_filepath (str): path to a text file with recognized image content
        log (bool): set whether to print log messages (default True)
        do_correct (bool): set whether to ask user for correct values
            (default True)
        do_save (bool): set whether to save the extracted content to a JSON file
            (default True)
        output_filepath (str): path to the output file (default
            extracted_content.txt)

    Return:
        dict: dictionary with extracted content

    """
    # Read raw content
    raw_content = read_raw_content(input_filepath)

    # Replace common wrong characters
    content = replace_invalid_chars(raw_content)

    # Get shop name
    shop_name = get_shop_name(raw_content, do_correct=do_correct)

    # Get items
    items = get_items(content, log=log, do_correct=do_correct)

    # Get total sum
    total_sum = get_total_sum(raw_content, do_correct=do_correct)

    # Set result dictionary
    extracted_content = {
        'content_filepath': input_filepath,
        'shop_name':        shop_name,
        'items':            items,
        'total_sum':        total_sum
    }

    if do_save is True:
        # Write recognized content to file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(extracted_content, f, indent=4)

        if log is True:
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
    output_filename = 'extracted_content.json'
    output_filepath = os.path.join(ROOT_FOLDERPATH,
                                   content_folderpath, output_filename)

    extract_content(content_filepath,
                    log=True, output_filepath=output_filepath)


if __name__ == '__main__':
    main()
