"""
Optical character recognition (OCR) for receipts processing.

Algorithm:
1. Apply perspective transformation to increase OCR accuracy
    1.1 Detect contours in the edge map
    1.2 Loop over contours and find the largest approximated contour with four
        vertices
    1.3 Apply a perspective transform, yielding a robust view of the receipt
2. Apply Tesseract OCR engine for character recognition
3. Use regular expressions to extract required data

The edge recognition and perspective transformation process will execute by
default. However, this step can be skipped using an argument.
"""
import os
import re
from pathlib import Path

import cv2 as cv
import imutils
import pytesseract
from imutils.perspective import four_point_transform

from setup import *

# Set input file path
img_filename = 'receipt.jpg'
img_filepath = Path('images/receipts') / img_filename

# Set directory to store processed images
proc_img_folder = Path('images/receipts_processed') / Path(img_filename).stem

# Set directory to store extracted text
result_folder = Path('results') / Path(img_filename).stem


def get_image(path):
    """Return an image from path."""
    img = cv.imread(str(path))
    print(f'Image was read from file "{path}"')

    return img


def resize_image(img):
    """Resize an image maintaining its aspect ratio."""
    global ratio

    img_resized = imutils.resize(img, width=500)
    ratio = img.shape[1] / float(img_resized.shape[1])

    return img_resized


def adjust_image(img):
    """Adjust image color to enhance contour detection."""
    grayed = cv.cvtColor(img, cv.COLOR_BGR2GRAY)   # convert to grayscale
    blurred = cv.GaussianBlur(grayed, (5, 5,), 0)  # blur using Gaussian kernel
    edged = cv.Canny(blurred, 75, 200)             # apply edge detection

    if DEBUG_MODE:
        cv.imshow('Edged', edged)
        cv.waitKey(0)

    return edged


def get_contour(img_ori, img_edged,
                save_outlined=DO_SAVE_CONTOUR_IMAGE,
                path=proc_img_folder / 'outlined.jpg'):
    """Find contours in image's edge map."""
    contours = cv.findContours(
        img_edged, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
    )
    contours = imutils.grab_contours(contours)

    # Sort contours according to their area size
    contours = sorted(contours, key=cv.contourArea, reverse=True)

    # Initialize a variable to store the contour
    contour = None

    for c in contours:
        # Approximate the contour by reducing the number of points
        peri = cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, 0.02 * peri, True)

        # If the approximated contour has 4 points...
        if len(approx) == 4:
            # ...we can assume it's the receipt's outline
            contour = approx
            break

    if contour is None:
        raise Exception('Could not find proper receipt contours. '
                        'Review the input image and try again.')

    outline = img_ori.copy()
    cv.drawContours(outline, [contour], -1, (0, 255, 0), 2)

    if DEBUG_MODE:
        cv.imshow('Receipt outline', outline)
        cv.waitKey(0)

    if save_outlined:
        cv.imwrite(str(path), outline)
        print(f'Image with detected outline was saved to the file "{path}"')

    return contour


def transform_image(img, contour,
                    save_transformed=DO_SAVE_TRANSFORMED_IMAGE,
                    path=proc_img_folder / 'transformed.jpg'):
    """Apply a four-point perspective transform to the original image."""
    transformed_img = four_point_transform(img, contour.reshape(4, 2) * ratio)

    if DEBUG_MODE:
        cv.imshow('Receipt transform', imutils.resize(transformed_img, width=500))
        cv.waitKey(0)

    if save_transformed:
        cv.imwrite(str(path), transformed_img)
        print(f'Transformed image was saved to the file "{path}"')

    return transformed_img


def prepare_image(img):
    """Prepare image for further processing."""
    resized = resize_image(img)
    edged = adjust_image(resized)

    contour = get_contour(resized, edged)

    return transform_image(img, contour)


def recognize_image(img,
                    write_content=DO_WRITE_PROCESSED_RECEIPT_TEXT,
                    path=result_folder / 'raw.txt'):
    """Execute OCR and return recognized content."""
    text = pytesseract.image_to_string(
        cv.cvtColor(img, cv.COLOR_BGR2RGB),
        config='--psm 4'
    )

    if write_content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Recognized image content was written to the file "{path}"')

    return text


def get_content(path, adjust=DO_ADJUST_IMAGE):
    """Get image text content."""
    raw_img = get_image(path)

    receipt = prepare_image(raw_img) if adjust else raw_img

    return recognize_image(receipt)


if DO_SAVE_CONTOUR_IMAGE or DO_SAVE_TRANSFORMED_IMAGE:
    try:
        os.makedirs(proc_img_folder)
    except OSError:
        print("Output directory already exists. "
              "All content will be overwritten.")

os.makedirs(result_folder, exist_ok=True)

text = get_content(img_filepath)
