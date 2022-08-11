"""
Script for extracting relevant data from text that was recognized based on
receipt image.
"""
import os
from pathlib import Path

# Set input file path
txt_content_filename = 'Paragon_2022-08-11_081131_300dpi.txt'
txt_content_filepath = Path('results') / txt_content_filename
