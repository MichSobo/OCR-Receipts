"""
Code for image processing and retrieving content with use of OCR methods.
"""
import os
import functools
from pathlib import Path

import cv2 as cv
import imutils
import pytesseract
from imutils.perspective import four_point_transform


# Set default paths
RAW_IMG_FOLDERPATH = r'..\images\receipts'
PROC_IMG_FOLDERPATH = r'..\images\receipts_processed'

# Set default options for debugging
DEBUG_MODE = True     # set whether to display processed images in runtime
SAVE_PROC_IMG = True  # set whether the processed images should be saved


def debug_image(func):
    """Function decorator for debugging purposes."""
    proc_img_name_mapper = {
        'resize_image': 'resized',
        'adjust_color': 'adjusted color',
        'draw_outline': 'outlined',
        'transform_image': 'transformed',
    }

    @functools.wraps(func)
    def wrapper_debug_image(img, *args, **kwargs):
        # Get the processed image by running a function
        proc_img = func(img, *args, **kwargs)

        if DEBUG_MODE:
            # Show the processed image during function execution
            proc_img_name = proc_img_name_mapper[func.__name__].capitalize()
            cv.imshow(proc_img_name, proc_img)
            cv.waitKey(0)

        if SAVE_PROC_IMG:
            # Save the processed image to a file
            proc_img_filename = proc_img_name_mapper[func.__name__] + '.jpg'
            proc_img_filepath = os.path.join(PROC_IMG_FOLDERPATH, proc_img_filename)

            cv.imwrite(proc_img_filepath, proc_img)
            print(f'Image was saved to file "{proc_img_filepath}"')

        return proc_img

    return wrapper_debug_image


def read_image(path):
    """Return an image read from path to the file."""
    img = cv.imread(path)
    print(f'Image was read from file "{path}"')

    return img


@debug_image
def resize_image(img):
    """Return a resized image maintaining its aspect ratio."""

    def get_ratio(first, second):
        """Return a ratio of two image sizes."""
        return float(first.shape[1]) / float(second.shape[1])

    img_resized = imutils.resize(img, width=500)

    # Get scaling ratio for further processing
    global ratio
    ratio = get_ratio(img, img_resized)

    return img_resized


@debug_image
def adjust_color(img):
    """Return an image with adjusted color to enhance contour detection."""
    img_grayed = cv.cvtColor(img, cv.COLOR_BGR2GRAY)       # convert to grayscale
    img_blurred = cv.GaussianBlur(img_grayed, (5, 5,), 0)  # blur using Gaussian kernel
    img_edged = cv.Canny(img_blurred, 75, 200)             # apply edge detection

    return img_edged


@debug_image
def draw_outline(img, contour):
    """Return an image with added contour layer."""
    img_outlined = img.copy()
    cv.drawContours(img_outlined, [contour], -1, (0, 255, 0), 2)

    return img_outlined


def get_contour(img):
    """Return a list of contours found in image's edge map."""
    # Find contours
    contours = cv.findContours(
        img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
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

    return contour


@debug_image
def transform_image(img, contour):
    """Return an image after four-point perspective transformation.

    Arguments:
        img (object): image to be transformed
        contour (list): contour definition

    Returns:
        object: transformed image
    """
    transformed_img = four_point_transform(img, contour.reshape(4, 2) * ratio)

    return transformed_img


def prepare_image(img):
    """Return an image prepared to enhance content recognition."""
    img_resized = resize_image(img)
    img_edged = adjust_color(img_resized)

    contour = get_contour(img_edged)
    img_outlined = draw_outline(img_resized, contour)

    img_transformed = transform_image(img, contour)

    return img_transformed


def recognize_image(img,
                    write_content=True,
                    content_path='content.txt'):
    """Execute OCR and return recognized content.

    Arguments:
        img (object): image for content recognition
        write_content (bool): set whether to write the recognized content to a
            text file (default True)
        content_path (str): path of the file to which the recognized content
            will be saved; if left blank, it will be saved in working directory
            as 'content.txt'

    Returns:
        list[str]: list of strings, where each string corresponds to a single
            line of the recognized content
    """
    # Execute OCR
    text = pytesseract.image_to_string(cv.cvtColor(img, cv.COLOR_BGR2RGB),
                                       config='--psm 4')

    if write_content:
        # Write the recognized content to a text file
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f'Recognized image content was written to file "{content_path}"')

    return text


def get_content(path, do_prepare_image=False):
    """Read and process an image. Return recognized text content.

    Arguments:
        path (str): path to the file with image
        do_prepare_image (bool): set whether to perform image preparation from
            prepare_image() (default False)

    Returns:
        list[str]: list of string elements, where each element corresponds to
            a single line of recognized content
    """
    raw_img = read_image(path)
    img = prepare_image(raw_img) if do_prepare_image else raw_img

    return recognize_image(img)


def main():
    # Set path to the raw image
    raw_img_filename = 'test1.jpg'
    raw_img_filepath = os.path.join(RAW_IMG_FOLDERPATH, raw_img_filename)

    # Read image
    raw_img = read_image(raw_img_filepath)

    if SAVE_PROC_IMG:
        filename, ext = os.path.splitext(raw_img_filename)

        # Set output folder for processed images
        global PROC_IMG_FOLDERPATH
        PROC_IMG_FOLDERPATH = os.path.join(PROC_IMG_FOLDERPATH, filename)

        # Create the output folder
        os.makedirs(PROC_IMG_FOLDERPATH, exist_ok=True)

    # resize_image = resize_image(raw_img)
    prepared_img = prepare_image(raw_img)

    # Recognize image content
    content = recognize_image(prepared_img)


if __name__ == '__main__':
    main()
