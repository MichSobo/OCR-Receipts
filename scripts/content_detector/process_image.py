"""
Code for image processing and retrieving content with use of OCR methods.

Content retrieving procedure:
1. Read the image
2. Prepare the image to improve OCR accuracy (optional step):
    2.1. Adjust image colors to enhance receipt's outline detection
    2.2. Apply edge detection to reveal the outline of the receipt
    2.3. Identify the largest, closed contour with four vertices
    2.4. Apply a perspective transformation to the image with detected contour
3. Use OCR (Tesseract engine with --psm 4) on the receipt to get the content
4. Save the content to file
"""
import argparse
import os
import functools
import sys

import cv2 as cv
import imutils
import pytesseract
from imutils.perspective import four_point_transform

LOG = True

# Set default paths
ROOT_FOLDERPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
RAW_IMG_FOLDERPATH = os.path.join(ROOT_FOLDERPATH, 'images/receipts')
PROC_IMG_FOLDERPATH = os.path.join(ROOT_FOLDERPATH, 'images/receipts_processed')
OUTPUT_FOLDERPATH = os.path.join(ROOT_FOLDERPATH, 'results')

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
        # Get the processed image by running appropriate function
        proc_img = func(img, *args, **kwargs)

        # Get kwargs if passed else get default
        debug_mode = kwargs.get('debug_mode', DEBUG_MODE)
        save_proc_img = kwargs.get('save_proc_img', SAVE_PROC_IMG)

        if debug_mode is True:
            # Show the processed image during function execution
            proc_img_name = proc_img_name_mapper[func.__name__].capitalize()
            cv.imshow(proc_img_name, proc_img)
            cv.waitKey(0)

        if save_proc_img is True:
            # Get output folder path if passed else get default
            proc_img_folderpath = kwargs.get('proc_img_folderpath', PROC_IMG_FOLDERPATH)
            os.makedirs(proc_img_folderpath, exist_ok=True)

            # Save the processed image to a file
            proc_img_filename = proc_img_name_mapper[func.__name__] + '.jpg'
            proc_img_filepath = os.path.join(proc_img_folderpath, proc_img_filename)

            cv.imwrite(proc_img_filepath, proc_img)

            if LOG:
                print(f'Image was saved to file "{os.path.abspath(proc_img_filepath)}"')

        return proc_img

    return wrapper_debug_image


def read_image(path):
    """Return an image read from path to the file."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f'No such file: "{os.path.abspath(path)}"')

    img = cv.imread(path)

    if LOG:
        print(f'Image was read from file "{os.path.abspath(path)}"')

    return img


@debug_image
def resize_image(img, debug=False, save_proc_img=False, proc_img_folderpath=None):
    """Return a resized image maintaining its aspect ratio.

    Arguments:
        img (object): image to be transformed
        debug (bool): set whether to display processed images at runtime
        save_proc_img (bool): set whether to save the processed images
        proc_img_folderpath (str): path to the folder, to which the processed
            images should be saved

    Returns:
        object: resized image
    """

    def get_ratio(first, second):
        """Return a ratio of two image sizes."""
        return float(first.shape[1]) / float(second.shape[1])

    img_resized = imutils.resize(img, width=500)

    # Get scaling ratio for further processing
    global ratio
    ratio = get_ratio(img, img_resized)

    return img_resized


@debug_image
def adjust_color(img, debug=False, save_proc_img=False, proc_img_folderpath=None):
    """Return an image with adjusted color to enhance contour detection.

    Arguments:
        img (object): image to be transformed
        debug (bool): set whether to display processed images at runtime
        save_proc_img (bool): set whether to save the processed images
        proc_img_folderpath (str): path to the folder, to which the processed
            images should be saved

    Returns:
        object: image with adjusted colors
    """
    img_grayed = cv.cvtColor(img, cv.COLOR_BGR2GRAY)      # convert to grayscale
    img_blurred = cv.GaussianBlur(img_grayed, (5, 5,), 0)  # blur using Gaussian kernel
    img_edged = cv.Canny(img_blurred, 75, 200)             # apply edge detection

    return img_edged


@debug_image
def draw_outline(img, contour, debug=False, save_proc_img=False, proc_img_folderpath=None):
    """Return an image with added contour layer.

    Arguments:
        img (object): image to be transformed
        contour (object): contour definition
        debug (bool): set whether to display processed images at runtime
        save_proc_img (bool): set whether to save the processed images
        proc_img_folderpath (str): path to the folder, to which the processed
            images should be saved

    Returns:
        object: image with detected contour
    """
    img_outlined = img.copy()
    cv.drawContours(img_outlined, [contour], -1, (0, 255, 0), 2)

    return img_outlined


def get_contour(img):
    """Return a list of contours found in image's edge map."""
    # Find contours
    contours = cv.findContours(img,
                                cv.RETR_EXTERNAL,
                                cv.CHAIN_APPROX_SIMPLE)
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
def transform_image(img, contour, debug=False, save_proc_img=False, proc_img_folderpath=None):
    """Return an image after four-point perspective transformation.

    Arguments:
        img (object): image to be transformed
        contour (object): contour definition
        debug (bool): set whether to display processed images at runtime
        save_proc_img (bool): set whether to save the processed images
        proc_img_folderpath (str): path to the folder, to which the processed
            images should be saved

    Returns:
        object: transformed image
    """
    transformed_img = four_point_transform(img, contour.reshape(4, 2) * ratio)

    return transformed_img


def prepare_image(img, **kwargs):
    """Return an image prepared to enhance content recognition."""
    img_resized = resize_image(img, **kwargs)
    img_edged = adjust_color(img_resized, **kwargs)

    contour = get_contour(img_edged)
    img_outlined = draw_outline(img_resized, contour, **kwargs)

    img_transformed = transform_image(img, contour, **kwargs)

    return img_transformed


def binarize_image(img, blur=(1, 1), threshold=185):
    """Return a binarized image to enhance content recognition."""
    blurred = cv.GaussianBlur(img, blur, 0)
    binarized = cv.threshold(blurred, threshold, 255, cv.THRESH_BINARY)[1]

    return binarized


def recognize_content(img):
    """Execute OCR and return recognized content."""
    text = pytesseract.image_to_string(cv.cvtColor(img, cv.COLOR_BGR2RGB),
                                       config='--psm 4')

    return text


def get_img_content(img_filepath,
                    prepare_img=False,
                    binarize_img=True,
                    write_content=True,
                    output_filepath='raw_content.txt'):
    """Read and process an image. Return recognized text content.

    Arguments:
        img_filepath (str): path to the file with image to be processed
        prepare_img (bool): set whether to perform image preparation from
            prepare_image() (default False)
        binarize_img (bool): set whether to perform image binarization
            (default False)
        write_content (bool): set whether to write the recognized content
            to a text file (default True)
        output_filepath (str): path of the file to which the recognized content
            will be saved; if left blank, it will be saved in working directory
            as 'raw_content.txt'

    Returns:
        list[str]: list of string elements, where each element corresponds to
            a single line of recognized content
    """
    # Get image
    raw_img = read_image(img_filepath)
    img = prepare_img(raw_img) if prepare_img else raw_img
    img = binarize_image(img) if binarize_img else img

    # Set output directory
    filename = os.path.basename(img_filepath)
    filename, _ = os.path.splitext(filename)
    output_folderpath = os.path.join(OUTPUT_FOLDERPATH, filename)
    os.makedirs(output_folderpath, exist_ok=True)

    # Recognize content
    content = recognize_content(img)

    # Write content to file
    if output_filepath == '':
        output_filepath = os.path.join(output_folderpath, 'raw_content.txt')

    if write_content is True:
        # Write recognized content to file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        if LOG is True:
            print(f'Recognized image content was written to file '
                  f'"{os.path.abspath(output_filepath)}"')

    return content


def main():
    # Set path to the raw image
    raw_img_filename = 'Paragon_2022-08-11_081131_300dpi.jpg'
    raw_img_filepath = os.path.join(RAW_IMG_FOLDERPATH, raw_img_filename)

    raw_content = get_img_content(raw_img_filepath)

    return raw_content


if __name__ == '__main__':
    # Set default options internal usage
    DEBUG_MODE = True         # set whether to display processed images at runtime
    SAVE_PROC_IMG = True      # set whether the processed images should be saved
    WRITE_IMG_CONTENT = True  # set whether the recognized content should be written

    if len(sys.argv) > 1:
        # Set command line argument parsing
        description = 'This program performs OCR on an input image and writes it.'
        parser = argparse.ArgumentParser(description=description)

        parser.add_argument('-i', '--image', required=True,
                            help='path to the input image')
        parser.add_argument('-o', '--output', required=False,
                            default='raw_content.txt',
                            help='path to the output file')
        parser.add_argument('-d', '--debug', action='store_true',
                            help='specify if interim images should be shown')

        args = parser.parse_args()

        raw_img_filepath = args.image
        output_filepath = args.output

        if args.debug is True:
            DEBUG_MODE = True

        get_img_content(raw_img_filepath, content_path=output_filepath)

    else:
        main()
else:
    # Set default options for external usage
    DEBUG_MODE = False
    SAVE_PROC_IMG = False
    WRITE_IMG_CONTENT = False



