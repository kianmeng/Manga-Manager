import os
import unittest
import zipfile
from unittest.mock import patch, MagicMock

import src.Common.LoadedComicInfo.LoadedComicInfo
from common.models import ComicInfo
from logging_setup import add_trace_level
from src.Common.LoadedComicInfo.LoadedComicInfo import LoadedComicInfo
from src.Common.errors import CorruptedComicInfo, NoComicInfoLoaded
from src.Common.errors import EditedCinfoNotSet, BadZipFile
from src.MetadataManager import MetadataManagerLib
from tests.common import create_dummy_files

add_trace_level()


class CoreTesting(unittest.TestCase):
    test_files_names = None

    @patch.multiple(MetadataManagerLib.MetadataManagerLib, __abstractmethods__=set())
    def setUp(self) -> None:
        self.instance = MetadataManagerLib.MetadataManagerLib()
        leftover_files = [listed for listed in os.listdir() if listed.startswith("Test__") and listed.endswith(".cbz")]
        for file in leftover_files:
            os.remove(file)

    def tearDown(self) -> None:
        # Some cases patch LoadedComicInfo. patchin back just in case
        src.Common.LoadedComicInfo.LoadedComicInfo.LoadedComicInfo = LoadedComicInfo
        print("Teardown:")
        for filename in self.test_files_names:
            print(f"     Deleting: {filename}")  # , self._testMethodName)
            try:
                os.remove(filename)
            except Exception as e:
                print(e)

    def test(self):
        out_tmp_zipname = f"random_image_1_not_image.ext.cbz"
        out_tmp_zipname2 = f"random_image_1_not_image.ext.cbz"
        self.test_files_names = []
        self.len_file_1 = 5
        with zipfile.ZipFile(out_tmp_zipname, "w") as zf:
            zf.writestr("Dummyfile.ext", "Dummy")
            zf.writestr("Dummyfile1.ext", "Dummy")
            zf.writestr("Dummyfile2.ext", "Dummy")
            zf.writestr("Dummyfile3.ext", "Dummy")
            zf.writestr("Dummyfile4.ext", "Dummy")
        self.test_files_names.append(out_tmp_zipname)
        self.len_file_2 = 5
        with zipfile.ZipFile(out_tmp_zipname2, "w") as zf:
            zf.writestr("Dummyfile.ext", "Dummy")
            zf.writestr("Dummyfile1.ext", "Dummy")
            zf.writestr("Dummyfile2.ext", "Dummy")
            zf.writestr("Dummyfile3.ext", "Dummy")
            zf.writestr("Dummyfile4.ext", "Dummy")
        print(f"     Creating: {out_tmp_zipname2}")  # , self._testMethodName)
        self.test_files_names.append(out_tmp_zipname2)
        # Create a random int so the values in the cinfo are unique each test

        # Create metadata objects
        cinfo_1 = ComicInfo()
        cinfo_1.series = "This series from file 1 should be kept"
        cinfo_1.writer = "This writer from file 1 should NOT be kept"

        cinfo_2 = ComicInfo()
        cinfo_2.series = "This series from file 2 should be kept"
        cinfo_2.writer = "This writer from file 2 should NOT be kept"

        # Created loaded metadata objects
        metadata_1 = LoadedComicInfo(out_tmp_zipname, comicinfo=cinfo_1)
        metadata_2 = LoadedComicInfo(out_tmp_zipname2, comicinfo=cinfo_2)

        self.instance.loaded_cinfo_list = [metadata_1, metadata_2]
        # There is no edited comicinfo, it should fail
        with self.assertRaises(EditedCinfoNotSet):
            self.instance.merge_changed_metadata(self.instance.loaded_cinfo_list)
        new_cinfo = ComicInfo()
        new_cinfo.series = self.instance.MULTIPLE_VALUES_CONFLICT
        new_cinfo.writer = "This is the new writer for both cinfo"
        self.instance.new_edited_cinfo = new_cinfo
        self.instance.merge_changed_metadata(self.instance.loaded_cinfo_list)
        print("Assert values are kept")
        self.assertEqual("This series from file 1 should be kept", metadata_1.cinfo_object.series)
        self.assertEqual("This series from file 2 should be kept", metadata_2.cinfo_object.series)
        print("Assert values are overwritten")
        self.assertEqual("This is the new writer for both cinfo", metadata_1.cinfo_object.writer)
        self.assertEqual("This is the new writer for both cinfo", metadata_2.cinfo_object.writer)

    def test_selected_files_loaded(self):

        # Setup
        self.test_files_names = create_dummy_files(2)
        self.instance.selected_files_path = self.test_files_names
        self.instance.open_cinfo_list(lambda : False)
        self.assertEqual(2, len(self.instance.loaded_cinfo_list))

    def test_process_should_raise_exception_if_no_new_cinfo(self):
        self.test_files_names = create_dummy_files(2)
        self.instance.selected_files_path = self.test_files_names
        self.assertRaises(NoComicInfoLoaded, self.instance.process)



class ErrorHandlingTests(unittest.TestCase):
    """
    This should test that all functions in the methods in MetadataManagerLib._IMetadataManagerLib interface are called
    """
    test_files_names = None

    def setUp(self) -> None:
        leftover_files = [listed for listed in os.listdir() if
                          listed.startswith("Test__") and listed.endswith(".cbz")]
        for file in leftover_files:
            os.remove(file)

    def tearDown(self) -> None:
        # Some cases patch LoadedComicInfo. patchin back just in case
        src.Common.LoadedComicInfo.LoadedComicInfo.LoadedComicInfo = LoadedComicInfo
        print("Teardown:")
        for filename in self.test_files_names:
            print(f"     Deleting: {filename}")  # , self._testMethodName)
            try:
                os.remove(filename)
            except Exception as e:
                print(e)
    @unittest.skip("Broken test")
    @patch.multiple(MetadataManagerLib.MetadataManagerLib, __abstractmethods__=set())
    def test_load_files_should_handle_broken_zipfile(self):
        self.instance = MetadataManagerLib.MetadataManagerLib()

        class RaiseBadZip:
            ...

        def raise_badzip(*_, **__):
            raise BadZipFile()

        RaiseBadZip.__init__ = raise_badzip
        src.Common.LoadedComicInfo.LoadedComicInfo.LoadedComicInfo = RaiseBadZip

        self.instance.selected_files_path = self.test_files_names = create_dummy_files(2)

        self.instance.on_badzipfile_error = MagicMock()
        self.instance.open_cinfo_list()
        self.instance.on_badzipfile_error.assert_called()

    @unittest.skip("Broken test")
    @patch.multiple(MetadataManagerLib.MetadataManagerLib, __abstractmethods__=set())
    def test_on_badzipfile_error(self):
        self.instance = MetadataManagerLib.MetadataManagerLib()

        class RaiseCorruptedMeta:
            ...

        def raise_badzip(*_, **__):
            # Exception raised but then we create a new object with a brand new comicinfo.
            # Fix back patched class and raise exception
            src.Common.LoadedComicInfo.LoadedComicInfo.LoadedComicInfo = LoadedComicInfo
            raise CorruptedComicInfo("")

        RaiseCorruptedMeta.__init__ = raise_badzip
        src.Common.LoadedComicInfo.LoadedComicInfo.LoadedComicInfo = RaiseCorruptedMeta

        self.instance.selected_files_path = self.test_files_names = create_dummy_files(2)

        self.instance.on_corruped_metadata_error = MagicMock()
        self.instance.open_cinfo_list()
        self.instance.on_corruped_metadata_error.assert_called()

    @patch.multiple(MetadataManagerLib.MetadataManagerLib, __abstractmethods__=set())
    def test_on_writing_error(self):
        self.instance = MetadataManagerLib.MetadataManagerLib()
        called = False
        class RaisePermissionError(LoadedComicInfo):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.has_changes = True

            def write_metadata(self, auto_unmark_changes=False):
                if not called:
                    raise PermissionError("This exception is raised as part of one unit test. Safe to ignore")
                else:
                    super().write_metadata(auto_unmark_changes)
                

        src.Common.LoadedComicInfo.LoadedComicInfo.LoadedComicInfo = RaisePermissionError

        self.instance.selected_files_path = self.test_files_names = create_dummy_files(2)
        self.instance.loaded_cinfo_list = [RaisePermissionError(path) for path in self.test_files_names]
        self.instance.new_edited_cinfo = ComicInfo()
        self.instance.on_writing_error = MagicMock()
        self.instance.process()
        self.instance.on_writing_error.assert_called()

    @patch.multiple(MetadataManagerLib.MetadataManagerLib, __abstractmethods__=set())
    def test_on_writing_exception(self):
        self.instance = MetadataManagerLib.MetadataManagerLib()

        class RaisePermissionError(LoadedComicInfo):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.has_changes = True

            def write_metadata(self, auto_unmark_changes=False):
                raise Exception("Exception. This exception is raised as part of one unit test. Safe to ignore")

        src.Common.LoadedComicInfo.LoadedComicInfo.LoadedComicInfo = RaisePermissionError

        self.instance.selected_files_path = self.test_files_names = create_dummy_files(2)
        self.instance.loaded_cinfo_list = [RaisePermissionError(path) for path in self.test_files_names]
        self.instance.new_edited_cinfo = ComicInfo()
        self.instance.on_writing_exception = MagicMock()
        self.instance.process()
        self.instance.on_writing_exception.assert_called()
