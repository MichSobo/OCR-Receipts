"""
Code for image processing and retrieving content with use of OCR methods.
"""
import os
import functools

import cv2 as cv
import imutils
import pytesseract
from imutils.perspective import four_point_transform


# Set default paths
RAW_IMG_FOLDERPATH = r'..\images\receipts'
PROC_IMG_FOLDERPATH = r'..\images\receipts_processed'
OUTPUT_FOLDERPATH = r'..\results'

# Set default options for debugging
DEBUG_MODE = True         # set whether to display processed images in runtime
SAVE_PROC_IMG = True      # set whether the processed images should be saved
WRITE_IMG_CONTENT = True  # set whether the recognized content should be written


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

        # Get arguments kwargs if passed else get default
        debug_mode = kwargs.get('debug_mode', DEBUG_MODE)
        save_proc_img = kwargs.get('save_proc_img', SAVE_PROC_IMG)

        if debug_mode:
            # Show the processed image during function execution
            proc_img_name = proc_img_name_mapper[func.__name__].capitalize()
            cv.imshow(proc_img_name, proc_img)
            cv.waitKey(0)

        if save_proc_img:
            # Get output folder path if passed else get default
            proc_img_folderpath = kwargs.get('path', PROC_IMG_FOLDERPATH)

            # Save the processed image to a file
            proc_img_filename = proc_img_name_mapper[func.__name__] + '.jpg'
            proc_img_filepath = os.path.join(proc_img_folderpath, proc_img_filename)

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
def resize_image(img, **kwargs):
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
def adjust_color(img, **kwargs):
    """Return an image with adjusted color to enhance contour detection."""
    img_grayed = cv.cvtColor(img, cv.COLOR_BGR2GRAY)       # convert to grayscale
    img_blurred = cv.GaussianBlur(img_grayed, (5, 5,), 0)  # blur using Gaussian kernel
    img_edged = cv.Canny(img_blurred, 75, 200)             # apply edge detection

    return img_edged


@debug_image
def draw_outline(img, contour, **kwargs):
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
def transform_image(img, contour, **kwargs):
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


def recognize_img_content(img,
                          write_img_content=True,
                          content_path='raw_content.txt'):
    """Execute OCR and return recognized content.

    Arguments:
        img (object): image for content recognition
        write_img_content (bool): set whether to write the recognized content
            to a text file (default True)
        content_path (str): path of the file to which the recognized content
            will be saved; if left blank, it will be saved in working directory
            as 'raw_content.txt'

    Returns:
        list[str]: list of strings, where each string corresponds to a single
            line of the recognized content
    """
    # Execute OCR
    text = pytesseract.image_to_string(cv.cvtColor(img, cv.COLOR_BGR2RGB),
                                       config='--psm 4')

    if write_img_content:
        # Write recognized content to a text file
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f'Recognized image content was written to file "{content_path}"')

    return text


def get_img_content(img_filepath, do_prepare_image=False):
    """Read and process an image. Return recognized text content.

    Arguments:
        img_filepath (str): path to the file with image to be processed
        do_prepare_image (bool): set whether to perform image preparation from
            prepare_image() (default False)

    Returns:
        list[str]: list of string elements, where each element corresponds to
            a single line of recognized content
    """
    raw_img = read_image(img_filepath)
    img = prepare_image(raw_img) if do_prepare_image else raw_img

    return recognize_img_content(img)


def main():
    # Set path to the raw image
    raw_img_filename = 'test1.jpg'
    raw_img_filepath = os.path.join(RAW_IMG_FOLDERPATH, raw_img_filename)
    filename, ext = os.path.splitext(raw_img_filename)

    # Read image
    raw_img = read_image(raw_img_filepath)

    if SAVE_PROC_IMG:
        # Set output folder for processed images
        global PROC_IMG_FOLDERPATH
        PROC_IMG_FOLDERPATH = os.path.join(PROC_IMG_FOLDERPATH, filename)

        # Create the output folder
        os.makedirs(PROC_IMG_FOLDERPATH, exist_ok=True)

    prepared_img = prepare_image(raw_img)

    # Recognize image content and write it to a file
    if WRITE_IMG_CONTENT:
        # Set output folder for recognized content
        global OUTPUT_FOLDERPATH
        OUTPUT_FOLDERPATH = os.path.join(OUTPUT_FOLDERPATH, filename)

        # Create the output folder
        os.makedirs(OUTPUT_FOLDERPATH, exist_ok=True)

        raw_content_filepath = os.path.join(OUTPUT_FOLDERPATH, 'raw_content.txt')

    raw_content = recognize_img_content(prepared_img,
                                        write_img_content=WRITE_IMG_CONTENT,
                                        content_path=raw_content_filepath)

    return raw_content


if __name__ == '__main__':
    main()
else:
    # Set default options for external usage
    DEBUG_MODE = False
    SAVE_PROC_IMG = False
    WRITE_IMG_CONTENT = False
