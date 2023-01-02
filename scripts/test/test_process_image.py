"""
Code for process_image.py unit testing.
"""
import os
import unittest

from scripts.content_detector import process_image
process_image.LOG = False

CLEANUP = True

TEST_IMG_FILEPATH = 'test_img.jpg'

ARBITRARY_PROC_IMG_FOLDERPATH = './images/receipts_processed'


def setUpModule():
    """Read the test image."""
    global img
    img = process_image.read_image(TEST_IMG_FILEPATH)


class TestReadImage(unittest.TestCase):
    """Test case for read_image()"""

    def test_case01(self):
        """test with not existing file"""
        self.assertRaises(FileNotFoundError,
                          process_image.read_image,
                          'not_existing_file.jpg')


class TestResizeImage(unittest.TestCase):
    """Test case for resize_image()"""
    default_proc_img_folderpath = process_image.PROC_IMG_FOLDERPATH
    default_proc_img_filepath = os.path.join(process_image.PROC_IMG_FOLDERPATH,
                                             'resized.jpg')
    arbitrary_proc_img_filepath = os.path.join(ARBITRARY_PROC_IMG_FOLDERPATH,
                                               'resized.jpg')

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(cls.default_proc_img_filepath):
            os.remove(cls.default_proc_img_filepath)
        if os.path.isfile(cls.arbitrary_proc_img_filepath):
            os.remove(cls.arbitrary_proc_img_filepath)

        cls.file_to_remove = None

    def test_case01(self):
        """test with unsupported object"""
        self.assertRaises(AttributeError,
                          process_image.resize_image,
                          'this is the image')

    def test_save01(self):
        """test with: save_proc_img default, proc_img_folderpath default"""
        process_image.resize_image(img)
        self.assertFalse(os.path.isfile(self.default_proc_img_filepath))

        self.file_to_remove = None

    def test_save02(self):
        """test with: save_proc_img default, proc_img_folderpath arbitrary"""
        process_image.resize_image(img,
                                   proc_img_folderpath=ARBITRARY_PROC_IMG_FOLDERPATH)
        self.assertFalse(os.path.isfile(self.arbitrary_proc_img_filepath))

        self.file_to_remove = None

    def test_save03(self):
        """test with: save_proc_img True, proc_img_folderpath default"""
        process_image.resize_image(img, save_proc_img=True)
        self.assertTrue(os.path.isfile(self.default_proc_img_filepath))

        self.file_to_remove = self.default_proc_img_filepath

    def test_save04(self):
        """test with: save_proc_img True, proc_img_folderpath arbitrary"""
        process_image.resize_image(img,
                                   save_proc_img=True,
                                   proc_img_folderpath=ARBITRARY_PROC_IMG_FOLDERPATH)
        self.assertTrue(os.path.isfile(self.arbitrary_proc_img_filepath))

        self.file_to_remove = self.arbitrary_proc_img_filepath

    def test_save05(self):
        """test with: save_proc_img False, proc_img_folderpath default"""
        process_image.resize_image(img, save_proc_img=False)
        self.assertFalse(os.path.isfile(self.default_proc_img_filepath))

        self.file_to_remove = None

    def test_save06(self):
        """test with: save_proc_img False, proc_img_folderpath arbitrary"""
        process_image.resize_image(img,
                                   save_proc_img=False,
                                   proc_img_folderpath=ARBITRARY_PROC_IMG_FOLDERPATH)
        self.assertFalse(os.path.isfile(self.arbitrary_proc_img_filepath))
        self.file_to_remove = None

    def tearDown(self):
        if self.file_to_remove and CLEANUP is True:
            os.remove(self.file_to_remove)


class TestPrepareImage(unittest.TestCase):
    """Test case for prepare_image()"""

    default_proc_img_folderpath = process_image.PROC_IMG_FOLDERPATH
    default_proc_img_filepaths = [
        os.path.join(default_proc_img_folderpath, 'resized.jpg'),
        os.path.join(default_proc_img_folderpath, 'adjusted color.jpg'),
        os.path.join(default_proc_img_folderpath, 'outlined.jpg'),
        os.path.join(default_proc_img_folderpath, 'transformed.jpg'),
    ]

    arbitrary_proc_img_filepaths = [
        os.path.join(ARBITRARY_PROC_IMG_FOLDERPATH, 'resized.jpg'),
        os.path.join(ARBITRARY_PROC_IMG_FOLDERPATH, 'adjusted color.jpg'),
        os.path.join(ARBITRARY_PROC_IMG_FOLDERPATH, 'outlined.jpg'),
        os.path.join(ARBITRARY_PROC_IMG_FOLDERPATH, 'transformed.jpg'),
    ]

    @classmethod
    def setUpClass(cls):
        """Make a directory for storing test images if not exists, refresh content."""
        os.makedirs(ARBITRARY_PROC_IMG_FOLDERPATH, exist_ok=True)

        for filepath in cls.default_proc_img_filepaths + cls.arbitrary_proc_img_filepaths:
            if os.path.isfile(filepath):
                os.remove(filepath)

        cls.files_to_remove = None

    def test_case01(self):
        """test with unsupported object"""
        self.assertRaises(AttributeError,
                          process_image.prepare_image,
                          'this is the image')

    def test_save01(self):
        """test with: save_proc_img default, proc_img_folderpath default"""
        process_image.prepare_image(img)

        self.assertFalse('resized.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertFalse('adjusted color.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertFalse('outlined.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertFalse('transformed.jpg' in os.listdir(self.default_proc_img_folderpath))

        self.files_to_remove = None

    def test_save02(self):
        """test with: save_proc_img default, proc_img_folderpath arbitrary"""
        process_image.prepare_image(img,
                                    proc_img_folderpath=ARBITRARY_PROC_IMG_FOLDERPATH)

        self.assertFalse('resized.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertFalse('adjusted color.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertFalse('outlined.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertFalse('transformed.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))

        self.files_to_remove = None

    def test_save03(self):
        """test with: save_proc_img True, proc_img_folderpath default"""
        process_image.prepare_image(img, save_proc_img=True)

        self.assertTrue('resized.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertTrue('adjusted color.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertTrue('outlined.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertTrue('transformed.jpg' in os.listdir(self.default_proc_img_folderpath))

        self.files_to_remove = self.default_proc_img_filepaths

    def test_save04(self):
        """test with: save_proc_img True, proc_img_folderpath arbitrary"""
        process_image.prepare_image(img,
                                    save_proc_img=True,
                                    proc_img_folderpath=ARBITRARY_PROC_IMG_FOLDERPATH)

        self.assertTrue('resized.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertTrue('adjusted color.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertTrue('outlined.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertTrue('transformed.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))

        self.files_to_remove = self.arbitrary_proc_img_filepaths

    def test_save05(self):
        """test with: save_proc_img False, proc_img_folderpath default"""
        process_image.prepare_image(img, save_proc_img=False)

        self.assertFalse('resized.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertFalse('adjusted color.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertFalse('outlined.jpg' in os.listdir(self.default_proc_img_folderpath))
        self.assertFalse('transformed.jpg' in os.listdir(self.default_proc_img_folderpath))

        self.files_to_remove = None

    def test_save06(self):
        """test with: save_proc_img False, proc_img_folderpath arbitrary"""
        process_image.prepare_image(img,
                                    save_proc_img=False,
                                    proc_img_folderpath=ARBITRARY_PROC_IMG_FOLDERPATH)
        self.assertFalse('resized.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertFalse('adjusted color.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertFalse('outlined.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))
        self.assertFalse('transformed.jpg' in os.listdir(ARBITRARY_PROC_IMG_FOLDERPATH))

        self.files_to_remove = None

    def tearDown(self):
        """Remove generated images."""
        if self.files_to_remove and CLEANUP is True:
            for filepath in self.files_to_remove:
                os.remove(filepath)

    @classmethod
    def tearDownClass(cls):
        """Remove the directory to store test images."""
        os.rmdir(ARBITRARY_PROC_IMG_FOLDERPATH)


class TestRecognizeContent(unittest.TestCase):
    """Test case for recognize_img_content()"""

    default_filename = 'raw_content.txt'
    arbitrary_filename = 'arbitrary.txt'

    @classmethod
    def setUpClass(cls):
        # Remove files from directory if already exist
        if os.path.isfile(cls.default_filename):
            os.remove(cls.default_filename)

        if os.path.isfile(cls.arbitrary_filename):
            os.remove(cls.arbitrary_filename)

    def test_save01(self):
        """test saving with: default write_content, default content_path"""
        self.filename = self.__class__.default_filename
        process_image.recognize_content(img)

        self.assertTrue(self.filename in os.listdir())

    def test_save02(self):
        """test saving with: default write_content, arbitrary content_path"""
        self.filename = self.__class__.arbitrary_filename
        process_image.recognize_content(img, content_path=self.filename)

        self.assertTrue(self.filename in os.listdir())

    def test_save03(self):
        """test saving with: True write_content, default content_path"""
        self.filename = 'raw_content.txt'
        process_image.recognize_content(img, write_content=True)

        self.assertTrue(self.filename in os.listdir())

    def test_save04(self):
        """test saving with: True write_content, arbitrary content_path"""
        self.filename = self.__class__.arbitrary_filename
        process_image.recognize_content(img, write_content=True, content_path=self.filename)

        self.assertTrue(self.filename in os.listdir())

    def test_save05(self):
        """test saving with: False write_content, default content_path"""
        self.filename = self.__class__.default_filename
        process_image.recognize_content(img, write_content=False)

        self.assertFalse(self.filename in os.listdir())

    def test_save06(self):
        """test saving with: False write_content, arbitrary content_path"""
        self.filename = self.__class__.arbitrary_filename
        process_image.recognize_content(img, write_content=False, content_path=self.filename)

        self.assertFalse(self.filename in os.listdir())

    def tearDown(self):
        try:
            os.remove(self.filename)
        except FileNotFoundError:
            pass


class TestGetContent(unittest.TestCase):
    """Test case for get_img_content()."""

    output_filepath = r'../../results/test_img/raw_content.txt'

    @classmethod
    def setUpClass(cls):
        if os.path.isfile(cls.output_filepath):
            os.remove(cls.output_filepath)

    def test_case01(self):
        """test with: not existing file"""
        self.assertRaises(FileNotFoundError,
                          process_image.get_img_content,
                          'not_existing.jpg')

    def test_case02(self):
        """test with: default do_prepare_img"""
        process_image.get_img_content(TEST_IMG_FILEPATH)

        self.assertTrue(os.path.isfile(self.output_filepath))

        os.remove(self.output_filepath)

    def test_case03(self):
        """test with: True do_prepare_img"""
        process_image.get_img_content(TEST_IMG_FILEPATH, True)

        self.assertTrue(os.path.isfile(self.output_filepath))

        os.remove(self.output_filepath)

    def test_case04(self):
        """test with: False do_prepare_img"""
        process_image.get_img_content(TEST_IMG_FILEPATH, False)

        self.assertTrue(os.path.isfile(self.output_filepath))

        os.remove(self.output_filepath)


if __name__ == '__main__':
    unittest.main()
