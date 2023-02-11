"""
Code for processing the extracted content of a receipt.
"""
import json
import os

import pandas as pd


def get_content(filepath):
    """Read a JSON file with extracted content and return it as a dictionary."""
    with open(filepath) as f:
        content = json.load(f)

    abspath = os.path.abspath(filepath)
    print(f'Extracted content was read from file "{abspath}"')

    return content


def main():
    # Set default paths
    ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..'))

    content_folderpath = os.path.join(ROOT_FOLDERPATH, 'results',
                                      'Paragon_2022-08-11_081131_300dpi')

    # Get extracted content
    content_filepath = os.path.join(content_folderpath, 'extracted_content.json')
    content = get_content(content_filepath)


if __name__ == '__main__':
    main()