"""
Code for processing the extracted content of a receipt.

Code allows to check the validity of extracted content and fix detected
discrepancies.
"""
import json
import os

import pandas as pd

from scripts.content_detector.process_raw_content import string_to_float


def get_content(filepath):
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
        return wrong_disc_items_df

    # Correct wrong properties
    props = ['total_price', 'total_discount', 'final_price']
    new_disc_items_df = wrong_disc_items_df.copy()
    for i in new_disc_items_df.index:
        item = new_disc_items_df.loc[i]

        while True:
            print(f'\n{item[["name", *props]]}')

            values = {}

            for prop in props:
                print(f'\nProperty: "{prop}", Value: {item[prop]}')

                # Set new value or skip
                value = input('Enter a new value or press Enter to skip: ')
                if value == '':
                    values[prop] = item[prop]
                else:
                    values[prop] = string_to_float(value)

            # Check if new values are correct
            is_correct = (round(values['total_price'] -
                                values['total_discount'], 2) ==
                          values['final_price'])
            if is_correct:
                break
            else:
                print('Properties were not set correctly. Try again...')

        # Set correct values in new DataFrame
        new_disc_items_df.loc[i, props] = values

    if inplace:
        # Update the reference DataFrame with new values
        df.update(new_disc_items_df[props])

    return new_disc_items_df


def main():
    # Set default paths
    ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..'))

    content_folderpath = os.path.join(ROOT_FOLDERPATH, 'results',
                                      'Paragon_2022-08-11_081131_300dpi')

    # Get extracted content
    content_filepath = os.path.join(content_folderpath, 'extracted_content.json')
    content = get_content(content_filepath)

    # Put items in DataFrame
    items_df = pd.DataFrame(content['items'])

    # Set missing properties if any exist
    missing_properties_df = correct_missing_properties(items_df, inplace=True)

    # Correct wrong properties for discounted items, if any exist
    wrong_disc_items_df = correct_discounted_items(items_df, inplace=True)

    # TODO: Check if qty * unit price = total price

    # TODO: Correct wrong properties

    # TODO: Check if extracted total sum = calculated total sum

    # TODO: Check if total sum was extracted correctly

    # TODO: Check on receipt if any items missing

    # TODO: Allow to add items





if __name__ == '__main__':
    main()