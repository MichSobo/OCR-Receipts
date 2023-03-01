"""
Code for processing the extracted content of a receipt.

Code allows to check the validity of extracted content and fix detected
discrepancies.
"""
import json
import os

import numpy as np
import pandas as pd
import pyinputplus as pyip

from scripts.content_detector.misc import string_to_float


def read_content(filepath):
    """Read a JSON file with extracted content and return it as a dictionary."""
    with open(filepath) as f:
        content = json.load(f)

    abspath = os.path.abspath(filepath)
    print(f'Extracted content was read from file "{abspath}"')

    return content


def get_missing_properties(df):
    """Return DataFrame with items that are missing properties."""
    return df.copy().loc[(df == False).any(axis=1)]


def correct_missing_properties(df, inplace=False):
    """Return DataFrame with missing properties filled in.

    The property is assumed to be missing when its value is False.

    Arguments:
        df (pd.DataFrame): reference DataFrame with items
        inplace (bool): set whether to the reference DataFrame with new values
            (default False)

    Returns:
        pd.DataFrame: DataFrame with missing properties filled in
    """
    missing_properties_df = get_missing_properties(df)
    if len(missing_properties_df) > 0:
        print(f'\nFound items with missing properties...')
    else:
        return missing_properties_df

    for i in missing_properties_df.index:
        item = missing_properties_df.loc[i]
        print(f'\n{item}')

        # Get missing properties
        missing_properties = item.loc[item == False]

        # Set missing properties
        for prop, _ in missing_properties.items():
            print(f'\nIncorrect value for property "{prop}"')

            # Get new value
            value = string_to_float(input('Enter new value: '))

            # Set new value
            missing_properties_df.loc[i, prop] = value

    if inplace:
        # Update the reference DataFrame with new values
        df.update(missing_properties_df)

    return missing_properties_df


def get_discounted_items(df):
    """Return DataFrame with discounted items."""
    return df.copy().loc[~df['total_discount'].isna()]


def correct_discounted_items(df, inplace=False):
    """Return DataFrame with corrected wrong properties for discounted items.

    The function checks the difference between calculated final price and
    extracted final price for discounted items.

    Arguments:
        df (pd.DataFrame): reference DataFrame with items
        inplace (bool): set whether to the reference DataFrame with new values
            (default False)

    Returns:
        pd.DataFrame: DataFrame with corrected discounted items
    """
    disc_items_df = get_discounted_items(df)

    # Get calculated final price
    calc_final_price = round(disc_items_df['total_price'] -
                             disc_items_df['total_discount'], 2)

    # Get wrong items by comparing calculated price with extracted price
    wrong_disc_items_df = disc_items_df.loc[
        disc_items_df['final_price'] != calc_final_price]
    if len(wrong_disc_items_df) > 0:
        print(f'\nFound discounted items with incorrect properties...')
    else:
        return disc_items_df

    # Correct wrong properties
    props = ['total_price', 'total_discount', 'final_price']

    correct_disc_items_df = wrong_disc_items_df.copy()
    for i in correct_disc_items_df.index:
        # Get item
        item = correct_disc_items_df.loc[i]

        # Get correct values for item's properties
        values = get_new_values(item, is_final_price_correct, props)

        # Set correct values in new DataFrame
        correct_disc_items_df.loc[i, props] = values

    if inplace:
        # Update the reference DataFrame with new values
        df.update(correct_disc_items_df[props])

    return correct_disc_items_df


def correct_wrong_items(df, inplace=False):
    """Return DataFrame with corrected wrong properties for all items.

    The function checks the difference between calculated total price and
    extracted final price, including discount.

    Arguments:
        df (pd.DataFrame): reference DataFrame with items
        inplace (bool): set whether to update the reference DataFrame with new
            values (default False)

    Returns:
        pd.DataFrame: DataFrame with corrected items
    """
    # Get calculated total price
    calc_total_price = round(df['qty'] * df['unit_price'], 2)

    # Get wrong items by comparing calculated price with extracted price
    wrong_items_df = df.loc[df['total_price'] != calc_total_price]
    if len(wrong_items_df) > 0:
        print(f'\nFound items with incorrect properties...')
    else:
        return wrong_items_df

    # Correct wrong properties
    props_total_price = ['qty', 'unit_price', 'total_price']
    props_final_price = ['total_discount', 'final_price']

    correct_items_df = wrong_items_df.copy()
    for i in correct_items_df.index:
        # Get item
        item = wrong_items_df.loc[i]

        # Check if it's a discounted item
        is_discounted = not pd.isna(item['total_discount'])

        # Get correct values for item's properties
        values = get_new_values(item, is_total_price_correct, props_total_price)

        if is_discounted:
            # Check if discount and final price are correct
            is_correct = is_final_price_correct({
                'total_price': values['total_price'],
                'total_discount': item['total_discount'],
                'final_price': item['final_price']
            })
            if not is_correct:
                print('Other properties seem to be set incorrectly...')

                # Get correct values for discounted item's properties
                disc_values = get_new_values(
                    item,
                    is_final_price_correct,
                    props_final_price,
                    initial_values={'total_price': values['total_price']}
                )
                values.update(disc_values)
        else:
            # Set total price as final price for non-discounted item
            values['final_price'] = values['total_price']

        # Set correct values in new DataFrame
        correct_items_df.loc[i, list(values.keys())] = values

    if inplace:
        # Update the reference DataFrame with new values
        df.update(correct_items_df)

    return correct_items_df


def is_final_price_correct(data):
    """Return True if final price is correct, False otherwise."""
    calculated = round(data['total_price'] - data['total_discount'], 2)
    extracted = data['final_price']

    return True if calculated == extracted else False


def is_total_price_correct(data):
    """Return True if total price is correct, False otherwise."""
    calculated = round(data['qty'] * data['unit_price'], 2)
    extracted = data['total_price']

    return True if calculated == extracted else False


def get_new_values(item, func, props, initial_values=None):
    """Return new/correct values for an item's properties.

    Arguments:
        item (pd.Series): item
        func: function to use for checking if item properties are correct
        props (list[str]): list of properties to change
        initial_values (dict): dictionary with initial values (default None)

    Returns:
        dict: dictionary with key -> property name, value -> property value
    """
    if initial_values is None:
        initial_values = {}

    # Print item as Series
    print(f'\n{item[["name", *props]]}')

    while True:
        values = initial_values

        for prop in props:
            print(f'\nProperty: "{prop}", Value: {item[prop]}')

            # Set new value or skip
            value = input('Enter a new value or press Enter to skip: ')
            if value == '':
                values[prop] = item[prop]
            else:
                values[prop] = string_to_float(value)

        # Check if new values are correct
        is_correct = func(values)
        if is_correct:
            return values
        else:
            print('Properties were not set correctly. Try again...')


def get_new_item():
    """Return a dictionary with item properties."""
    print('\nSet properties for a new item')

    item = {}

    # Set name
    item['name'] = input('name: ')

    # Set qty
    item['qty'] = string_to_float(input('quantity: '))

    # Set unit price
    item['unit_price'] = string_to_float(input('unit price: '))

    # Evaluate and set total price
    item['total_price'] = round(item['qty'] * item['unit_price'], 2)
    print(f'total price: {item["total_price"]}')

    # Set discount
    discount = pyip.inputNum('total discount: ')
    item['total_discount'] = None if discount == 0 else discount

    # Evaluate and set final price
    if item['discount'] is None:
        item['final_price'] = item['total_price']
    else:
        item['final_price'] = item['total_price'] - item['total_discount']
        print(f'final price: {item["final_price"]}')

    return item


def get_total_sum_diff(content, items_df=None):
    """Return a difference between the extracted and calculated total sum."""
    if items_df is None:
        items_df = pd.DataFrame(content['items'])

    extr_total_sum = content['total_sum']
    calc_total_sum = items_df['final_price'].sum()

    diff = round(abs(extr_total_sum - calc_total_sum), 2)

    return diff


def write_content(obj, filepath, log=True):
    """Write an object to a JSON file."""
    # Convert NaN to None for *total_discount* property
    for item in obj['items']:
        if np.isnan(item['total_discount']):
            item['total_discount'] = None

    # Write recognized content to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=4)

    if log is True:
        abspath = os.path.abspath(filepath)
        print(f'\nExtracted content was written to file "{abspath}"')


def main():
    # Set default paths
    ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..'))

    content_folderpath = os.path.join(ROOT_FOLDERPATH, 'results',
                                      'Paragon_2022-08-11_081131_300dpi')

    output_filename = 'processed_extracted_content.json'
    output_filepath = os.path.join(content_folderpath, output_filename)

    # Get extracted content
    content_filepath = os.path.join(content_folderpath, 'extracted_content.json')
    content = read_content(content_filepath)

    # Put items in DataFrame
    items_df = pd.DataFrame(content['items'])

    # Set missing properties, if any exist
    correct_missing_properties(items_df, inplace=True)

    # Correct wrong properties for discounted items, if any exist
    correct_discounted_items(items_df, inplace=True)

    # Correct wrong properties for all items, if any exist
    correct_wrong_items(items_df, inplace=True)

    # Get list of items
    content['items'] = items_df.to_dict('records')

    while True:
        # Check if total sum is correct
        diff = get_total_sum_diff(content, items_df)

        if diff == 0:
            # Write processed content
            print('\nExtracted data seems to be correct.')
            write_content(content, output_filepath)

            break
        else:
            print('\nExtracted and calculated total sum are not equal')
            print(f'The difference is: {diff}')

            # Check if extracted total sum is correct
            print(f'\nExtracted total sum is: {content["total_sum"]}')
            is_correct = pyip.inputYesNo('Is it correct?\n')
            if is_correct == 'yes':
                print('\nPlease check if all items were added...')
                do_add_items = pyip.inputYesNo('\nDo you want to add more items?')
                if do_add_items == 'yes':
                    # Add more items
                    new_items = []
                    while True:
                        # Get new item
                        new_item = get_new_item()

                        # Add new item to list
                        new_items.append(new_item)

                        do_add_items = pyip.inputYesNo('\nDo you want to add more items?')
                        if do_add_items == 'no':
                            break
                else:
                    print('\nProcessed content with detected problems will be saved')

                    # Write processed content with errors
                    write_content(content, output_filepath)

                    break
            else:
                # Set correct total sum
                new_total_sum = string_to_float(input('\nSet correct total sum: '))
                content['total_sum'] = new_total_sum


if __name__ == '__main__':
    main()