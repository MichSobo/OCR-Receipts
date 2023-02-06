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

class Image:
    """Class that represents an image."""

    def __init__(self, img, name='Image'):
        self.img = img
        self.name = name

    def __repr__(self):
        return f'Image({self.name})'

    @classmethod
    def from_path(cls, path):
        """Initialize Image by reading an image from a path."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f'No such file: "{os.path.abspath(path)}"')

        img = cv.imread(path)

        if LOG:
            print(f'Image was read from file: "{os.path.abspath(path)}"')

        return cls(img)

    def show(self):
        cv.imshow(self.name, self.img)
        cv.waitKey(0)

    def debug(func):
        @functools.wraps(func)
        def wrapper_debug(self, *args, **kwargs):
            # Get processed image
            proc_img = func(self, *args, **kwargs)

            # Get kwargs if passed else get default
            do_debug = kwargs.get('debug', DEBUG_MODE)
            do_save_proc_img = kwargs.get('save', SAVE_PROC_IMG)

            if do_debug is True:
                proc_img.show()

            if do_save_proc_img is True:
                # Get output folder path if passed else get default
                proc_img_folderpath = kwargs.get('proc_img_folderpath', '')
                if proc_img_folderpath != '':
                    os.makedirs(proc_img_folderpath, exist_ok=True)

                # Save the processed image
                proc_img_filename = proc_img.name + '.jpg'
                proc_img_filepath = os.path.join(proc_img_folderpath,
                                                 proc_img_filename)
                cv.imwrite(proc_img_filepath, proc_img.img)

                if LOG:
                    print(f'Image was saved to file "{os.path.abspath(proc_img_filepath)}"')

            return proc_img

        return wrapper_debug

    @debug
    def resize(self, debug=False, save=False, proc_img_folderpath=''):
        """Resize the image maintaining its aspect ratio.

        Arguments:
            debug (bool): set whether to display the resized image at run time
                (default False)
            save (bool): set whether to save the resized image (default False)
            proc_img_folderpath (str): path to the folder where the resized
                image will be saved (default cwd)

        Returns:
            object: resized image
        """

        def get_ratio(first, second):
            """Return a ratio of two image sizes."""
            return float(first.shape[1]) / float(second.shape[1])

        # Get resized image
        img_resized = imutils.resize(self.img, width=500)
        img_resized = self.__class__(img_resized)
        img_resized.name = 'Resized'

        # Set ratio
        global ratio
        ratio = get_ratio(self.img, img_resized.img)

        return img_resized

    @debug
    def adjust_color(self, debug=False, save=False, proc_img_folderpath=''):
        """Return an image with adjusted color to enhance contour detection.

        Arguments:
            debug (bool): set whether to display the adjusted image at run time
                (default False)
            save (bool): set whether to save the adjusted image (default False)
            proc_img_folderpath (str): path to the folder where the adjusted
                image will be saved (default cwd)

        Returns:
            object: image with adjusted colors
        """
        img_grayed = cv.cvtColor(self.img, cv.COLOR_BGR2GRAY)  # convert to grayscale
        img_blurred = cv.GaussianBlur(img_grayed, (5, 5,), 0)  # blur using Gaussian kernel
        img_edged = cv.Canny(img_blurred, 75, 200)             # apply edge detection
        img_edged = self.__class__(img_edged)
        img_edged.name = 'Edged'

        return img_edged

    def get_contour(self):
        """Return a list of contours found in image's edge map."""
        # Find contours
        contours = cv.findContours(self.img,
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

    @debug
    def outline(self, contour,
                debug=False, save=False, proc_img_folderpath=''):
        """Return an image with added contour layer.

        Arguments:
            contour (object): contour definition
            debug (bool): set whether to display the outlined image at run time
                (default False)
            save (bool): set whether to save the outlined image (default False)
            proc_img_folderpath (str): path to the folder where the outlined
                image will be saved (default cwd)

        Returns:
            object: image with detected contour
        """
        img_outlined = self.img.copy()
        cv.drawContours(img_outlined, [contour], -1, (0, 255, 0), 2)

        img_outlined = self.__class__(img_outlined)
        img_outlined.name = 'Outlined'

        return img_outlined

    @debug
    def transform(self, contour, debug=False, save=False, proc_img_folderpath=''):
        """Return an image after four-point perspective transformation.

        Arguments:
            contour (object): contour definition
            debug (bool): set whether to display the transformed image at run time
                (default False)
            save (bool): set whether to save the transformed image (default False)
            proc_img_folderpath (str): path to the folder where the transformed
                image will be saved (default cwd)

        Returns:
            object: transformed image
        """
        transformed_img = four_point_transform(self.img,
                                               contour.reshape(4, 2) * ratio)
        transformed_img = self.__class__(transformed_img)
        transformed_img.name = 'Transformed'

        return transformed_img

    def prepare(self, debug=False, save=False, proc_img_folderpath=''):
        """Return an image prepared to enhance content recognition."""
        kwargs = {
            'debug': debug,
            'save': save,
            'proc_img_folderpath': proc_img_folderpath
        }

        img_resized = self.resize(**kwargs)
        img_edged = img_resized.adjust_color(**kwargs)

        contour = img_edged.get_contour()

        img_outlined = img_resized.outline(contour, **kwargs)
        img_transformed = self.transform(contour, **kwargs)

        return img_transformed

    @debug
    def binarize(self, blur=(1, 1), threshold=185,
                 debug=False, save=False, proc_img_folderpath=''):
        """Return a binarized image to enhance content recognition."""
        blurred = cv.GaussianBlur(self.img, blur, 0)
        binarized = cv.threshold(blurred, threshold, 255, cv.THRESH_BINARY)[1]

        binarized = self.__class__(binarized)
        binarized.name = 'Binarized'

        return binarized

    def get_content(self, save=True, output_filepath='raw_content.txt'):
        """Execute OCR and return recognized content.

        Arguments:
            save (bool): set whether to save the recognized content to a file
                (default True)
            output_filepath (str): path to the output file (default raw_content.txt)
        """
        content = pytesseract.image_to_string(
            cv.cvtColor(self.img, cv.COLOR_BGR2RGB), config='--psm 4')

        if save is True:
            # Write recognized content to file
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            if LOG is True:
                print(f'Recognized image content was written to file '
                      f'"{os.path.abspath(output_filepath)}"')

        return content


def get_img_content(img_filepath,
                    debug=False,
                    prepare_img=False,
                    binarize_img=True,
                    save_proc_imgs=False,
                    proc_imgs_folderpath='',
                    write_content=True,
                    output_filepath=''):
    """Read and process an image. Return recognized text content.

    Arguments:
        img_filepath (str): path to the file with image to be processed
        debug (bool): set whether to display processed images at run time
        prepare_img (bool): set whether to perform image preparation from
            prepare_image() (default False)
        binarize_img (bool): set whether to perform image binarization
            (default False)
        save_proc_imgs (bool): set whether to save the processed images
            (default False)
        proc_imgs_folderpath (str): path to the folder where the processed
            images will be saved (default cwd)
        write_content (bool): set whether to write the recognized content
            to a text file (default True)
        output_filepath (str): path of the file to which the recognized content
            will be saved (name of the input image file with .txt extension
            by default)

    Returns:
        list[str]: list of string elements, where each element corresponds to
            a single line of recognized content
    """
    # Get raw image
    img = Image.from_path(img_filepath)

    # Get prepared image, if requested
    if prepare_img:
        img = img.prepare(debug=debug,
                          save=save_proc_imgs,
                          proc_img_folderpath=proc_imgs_folderpath)

    # Get binarized image, if requested
    if binarize_img:
        img = img.binarize(debug=debug,
                           save=save_proc_imgs,
                           proc_img_folderpath=proc_imgs_folderpath)

    # Set output file path
    if output_filepath == '':
        filename = os.path.splitext(os.path.basename(img_filepath))[0]
        output_filepath = filename + '.txt'

    # Recognize content
    content = img.get_content(write_content, output_filepath)

    return content


def main():
    # Set default paths
    ROOT_FOLDERPATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..'))
    RAW_IMG_FOLDERPATH = os.path.join(ROOT_FOLDERPATH, 'images/receipts')
    PROC_IMG_FOLDERPATH = os.path.join(ROOT_FOLDERPATH,
                                       'images/receipts_processed')
    OUTPUT_FOLDERPATH = os.path.join(ROOT_FOLDERPATH, 'results')

    # Set path to the raw image
    raw_img_filename = 'Paragon_2022-08-11_081131_300dpi.jpg'
    raw_img_filepath = os.path.join(RAW_IMG_FOLDERPATH, raw_img_filename)
    filename = os.path.splitext(os.path.basename(raw_img_filepath))[0]

    # Set path to processed images
    proc_imgs_folderpath = os.path.join(PROC_IMG_FOLDERPATH, filename)
    os.makedirs(proc_imgs_folderpath, exist_ok=True)

    # Set output directory
    output_folderpath = os.path.join(OUTPUT_FOLDERPATH, filename)
    os.makedirs(output_folderpath, exist_ok=True)

    # Set output file path
    output_filepath = os.path.join(output_folderpath, 'raw_content.txt')

    # Get content
    raw_content = get_img_content(raw_img_filepath,
                                  prepare_img=False,
                                  binarize_img=True,
                                  save_proc_imgs=True,
                                  proc_imgs_folderpath=proc_imgs_folderpath,
                                  output_filepath=output_filepath)

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

        get_img_content(raw_img_filepath, output_filepath=output_filepath)

    else:
        main()
else:
    # Set default options for external usage
    DEBUG_MODE = False
    SAVE_PROC_IMG = False
    WRITE_IMG_CONTENT = False



