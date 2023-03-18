"""
Code for defining application interface.
"""
import os
import shutil

import pyinputplus as pyip

from scripts import database
from scripts.content_processor import *


class Application:
    """Represents application."""

    MENU = {
        1: 'Extract receipt content',
        2: 'Save content to database',
        3: 'Show saved receipts',
        0: 'Exit'
    }

    def __init__(self, imgs_folderpath='', out_folderpath=''):
        print(f'\n{"=" * 24}\nOCR-Receipts Application')
        self.imgs_folderpath = imgs_folderpath
        self.raw_imgs_folderpath = os.path.join(imgs_folderpath, 'receipts')
        self.proc_imgs_folderpath = os.path.join(imgs_folderpath, 'receipts_processed')
        self.out_folderpath = out_folderpath

        # Create directories if not exist
        os.makedirs(self.raw_imgs_folderpath, exist_ok=True)
        os.makedirs(self.proc_imgs_folderpath, exist_ok=True)
        os.makedirs(self.out_folderpath, exist_ok=True)

        # Connect to database
        connection, cursor = database.connect(option_files='..\\..\\my.ini',
                                              database='shopping')
        self.connection = connection
        self.cursor = cursor

        # Initialize content
        self.content = None

    def __repr__(self):
        return f'Application(imgs_folderpath={self.imgs_folderpath}, out_folderpath{self.out_folderpath})'

    def menu(self):
        """Show application menu and get user inputs."""
        def show_menu():
            print('\nChoose an action from the list:')
            for option_id, option_text in Application.MENU.items():
                print(f'{option_id}. {option_text}')

        while True:
            show_menu()

            option_id = pyip.inputInt(min=0, max=3)

            if option_id == 1:
                self.extract_content()
            elif option_id == 2:
                self.save_content()
            elif option_id == 3:
                self.show_receipts()
            elif option_id == 0:
                self.exit()
                break
            else:
                raise NotImplementedError

    def extract_content(self):
        """Extract content of receipt image."""
        # Get image names from receipt images folder
        source_imgs = [filename for filename in os.listdir(self.raw_imgs_folderpath)
                       if os.path.splitext(filename)[1].lower()
                       in ('.jpg', '.jpeg', '.png')]

        # Get processed images from database
        db_imgs = database.get_receipts(self.cursor)

        # Get unprocessed images
        source_imgs_new = [filename for filename in source_imgs
                           if os.path.splitext(filename)[0]
                           not in os.listdir(self.out_folderpath)
                           and filename not in db_imgs]

        # Initialize img_filename variable
        img_filename = None

        if source_imgs_new:
            # Show them to user and ask if any of those should be used
            print('\nUnprocessed receipt images were found in local folder:')
            for i, filename in enumerate(source_imgs_new, start=1):
                print(f'{i}. {filename}')

            do_select = pyip.inputYesNo('\nDo you want to select any of the above?')
            if do_select == 'yes':
                if len(source_imgs_new) == 1:
                    img_filename = source_imgs_new[0]
                else:
                    selection = pyip.inputInt('Select corresponding number',
                                              min=1,
                                              max=len(source_imgs_new))
                    img_filename = source_imgs_new[selection - 1]

        if img_filename:
            img_filepath = os.path.join(self.raw_imgs_folderpath, img_filename)
        else:
            # Get path to image file
            while True:
                prompt = '\nEnter path to receipt image or press Enter to skip: '
                input_img_filepath = os.path.abspath(input(prompt))
                if input_img_filepath == '':
                    # Return to main menu
                    return None

                if os.path.isfile(input_img_filepath):
                    # If file exists, and it's an image, copy it to local folder
                    if (os.path.splitext(input_img_filepath)[1].lower()
                            in ('.jpg', '.jpeg', '.png')):
                        img_filename = os.path.basename(input_img_filepath)
                        img_filepath = os.path.join(self.raw_imgs_folderpath,
                                                    img_filename)

                        # Check if these are not the same files
                        if (img_filename in os.listdir(self.raw_imgs_folderpath)
                                or img_filename in db_imgs):
                            print('Looks like the image file was already processed')
                        else:
                            print(f'Copying file "{input_img_filepath}" to "{img_filepath}"')
                            shutil.copy2(input_img_filepath, img_filepath)
                            break
                    else:
                        print('Entered path does not refer to an image file')
                else:
                    print('Entered path does not refer to an existing file')

        # Set directories for output files
        proc_imgs_folderpath = os.path.join(self.proc_imgs_folderpath,
                                            os.path.splitext(img_filename)[0])
        os.makedirs(proc_imgs_folderpath)

        output_folderpath = os.path.join(self.out_folderpath,
                                         os.path.splitext(img_filename)[0])
        os.makedirs(output_folderpath)

        # Recognize image content
        raw_content = process_image.get_img_content(
            img_filepath,
            proc_imgs_folderpath=proc_imgs_folderpath,
            output_folderpath=output_folderpath
        )
        print('Image content was extracted')

        # Extract content from recognized text
        extracted_content = process_raw_content.extract_content(
            img_filepath,
            img_content=raw_content,
            output_folderpath=output_folderpath
        )

        # Process extracted content
        proc_extracted_content = process_extracted_content.process_content(
            extracted_content,
            output_folderpath=output_folderpath
        )
        self.content = proc_extracted_content

        do_write_db = pyip.inputYesNo('Do you want to save it to database?')
        if do_write_db == 'yes':
            self.save_content(proc_extracted_content)

        print(self.content)

    def save_content(self, content):
        """Save content to database."""
        print('Saving image')

    def show_receipts(self):
        """Print receipts data stored in database."""
        print('Showing saved receipts')

    def exit(self):
        """Exit application."""
        print('\nClosing application')


app = Application(imgs_folderpath='..\\..\\images',
                  out_folderpath='..\\..\\results')
app.menu()
