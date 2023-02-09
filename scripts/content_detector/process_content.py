"""
Script for extracting relevant data from recognized receipt content.
"""
import json
import os
import re


# Define regex patterns
ITEM_REGEX = re.compile(r'''
    (.+)                    # item name
    \s+\S{1,2}\s+           # char surrounded with spaces
    (\d+([,.]\s?\d+)?)      # quantity
    \sx?                    # "x"
    ([t\d]+[,.]\s?\d{0,2})  # item unit price
    \s+(\d+[,.]\s?\d{0,2})  # item total price
''', re.VERBOSE)

DISCOUNT_REGEX = re.compile(r'OPUST -?(\d+[,.]?\s?\d{0,2})')

PRICE_REGEX = re.compile(r'\d+[,.]\s?\d{0,2}')

QTY_PRICE_REGEX = re.compile(r'\s?,\s?')


def preprocess_text(text):
    """Return pre-processed text with replaced commonly incorrect characters."""
    new_text = text

    # Replace characters incorrectly recognized as "1"
    new_text = new_text.replace('(', '1')
    new_text = new_text.replace('{', '1')

    # Replace characters incorrectly recognized as "x"
    new_text = new_text.replace('«', 'x')
    new_text = new_text.replace('¥', 'x')

    # Replace characters incorrectly recognized as "-"
    new_text = new_text.replace('~', '-')

    # Replace characters incorrectly recognized as "?"
    new_text = new_text.replace('?', 'P')

    return new_text


def get_split_text(text, save=False, output_filepath=''):
    """Return a split text by new lines, considering discount."""
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


def get_shop_name(text, value_if_not_recognized=False):
    """Extract shop name from receipt's content.

    Return shop name if it exists in receipt text by comparing defined shop
    names with receipt content.
    In case of no match, str_if_not_recognized argument is returned.

    Arguments:
        text (str): input string for shop name extraction
        value_if_not_recognized (str): value to be returned if shop name is not
            found in the text (default False)

    Returns:
        str: recognized shop name, value_if_not_recognized otherwise
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

    return value_if_not_recognized


def string_to_float(string, log=True, item_string=None, do_correct=True):
    """Return float from string.

    Arguments:
        string (str): string to convert to float
        log (bool): set whether to print log messages (default True)
        item_string (str): string to be printed with error message (default None)
        do_correct (bool): set whether to ask user for correct values (default
            True)

    Returns:
        float if conversion was successful, False otherwise
    """

    def get_correct_value():
        """Get a correct value for quantity or price from user."""
        while True:
            user_input = input('\nEnter a valid number: ')
            try:
                float_user_input = float(user_input)
            except ValueError:
                print('Wrong input! Try again.')
            else:
                return float_user_input

    string = QTY_PRICE_REGEX.sub('.', string)

    try:
        value = float(string)
    except ValueError as e:
        if log:
            # Print log messages
            if item_string:
                print(f'\nError occurred for item: "{item_string}"')
            print(e)

        if do_correct:
            # Interactively get correct the value
            value = get_correct_value()
        else:
            value = False
    # except TypeError as e:
    #     if value is None:
    #         pass
    #     else:
    #         raise TypeError(e)
    finally:
        return value


def get_item(text, log=True, do_correct=True):
    """Return a dictionary with item properties."""
    result = ITEM_REGEX.match(text)
    if result is None:
        return None

    # Set item properties
    item = {
        'name': result.group(1),
        'qty': result.group(2),
        'unit_price': result.group(4),
        'total_price': result.group(5)
    }

    # Convert properties from string to numeric
    for key in list(item.keys())[1:]:
        value = string_to_float(item[key], log, text, do_correct)
        item[key] = value

    return item


def get_items(text, log=True, do_correct=True, write_raw=True, write_processed=True):
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
        do_correct (bool): set whether to ask user for correct values (default
            True)
        write_raw (bool): write matched regex pattern to raw_products.txt
            (default True)
        write_processed (bool): write processed matched items to
            processed_products.txt (default True)

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

        # Get additional properties
        if len(line) > 1:
            # Item with discount
            discount_line, final_price_line = line[1], line[2]
            discount = DISCOUNT_REGEX.search(discount_line).group(1)
            final_price = PRICE_REGEX.match(final_price_line).group()

            discount = string_to_float(discount, log, item_line, do_correct)
            final_price = string_to_float(final_price, log, item_line, do_correct)
        else:
            # Item without discount
            discount = None
            final_price = item['total_price']

        # Set additional properties
        item['total_discount'] = discount
        item['total_price_with_discount'] = final_price

        # Add item to list of items
        items.append(item)

    return items


def get_total_sum(text, value_if_not_recognized=False):
    """Return total shopping sum.

    Arguments:
        text (str): input string from which total cost will be extracted
        value_if_not_recognized (float): value to be returned if shop name is
            not found in the text (default False)

    Returns:
        float: recognized total sum, value_if_not_recognized otherwise
    """
    total_cost_regex = re.compile(r'SUMA\s+\w+\s+(\d+[,.]\d+)')
    match = total_cost_regex.search(text)

    if match:
        return string_to_float(match.group(1))
        # return float(match.group(1))
    else:
        return value_if_not_recognized


def main():
    # Set default paths
    ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..'))

    # Set path to raw content
    content_folderpath = 'results/Paragon_2022-08-11_081131_300dpi'
    content_filepath = os.path.join(ROOT_FOLDERPATH, content_folderpath, 'raw_content.txt')

    # Read raw content
    with open(content_filepath, encoding='utf-8') as f:
        raw_content = f.read()
    print(f'Raw content was read from file "{os.path.abspath(content_filepath)}"')

    # Get the main body of the receipt
    raw_content_main = raw_content.split('PARAGON FISKALNY\n')[1]

    # Replace common wrong characters
    content = preprocess_text(raw_content_main)

    # Get shop name
    shop_name = get_shop_name(raw_content)

    # Get items
    items = get_items(content,
                      log=True,
                      do_correct=False)

    # Get total sum
    total_sum = get_total_sum(raw_content_main)

    # Set result dictionary
    extracted_content = {
        'shop_name': shop_name,
        'items': items,
        'total_sum': total_sum
    }

    # Write extracted content to JSON file
    output_filename = 'extracted_content.json'
    output_filepath = os.path.join(ROOT_FOLDERPATH, content_folderpath, output_filename)
    with open(output_filepath, 'w') as f:
        json.dump(extracted_content, f, indent=4)

if __name__ == '__main__':
    main()
