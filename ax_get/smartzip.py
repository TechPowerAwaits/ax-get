# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

"""Provides a modified ZipFile class with more features."""

import os
import zipfile


class SmartZip(zipfile.ZipFile):
    def extractall(self, path=None, members=None, pwd=None, remove_parent=False):
        parent_dirs = []
        if remove_parent:
            for info_obj in self.infolist():
                # Only looking for the directories in the root
                # of the zip archive (whose filename would only
                # contain one path separator).
                if info_obj.is_dir() and info_obj.filename.count(os.path.sep) == 1:
                    parent_dirs.append(info_obj)
        super().extractall(path, members, pwd)
        if path is None:
            path = os.path.curdir
        if len(parent_dirs) == 1:
            parentname = parent_dirs[0].filename
            folder_loc = os.path.join(path, parentname)
            src_list = [
                os.path.join(folder_loc, _file) for _file in os.listdir(folder_loc)
            ]
            dest_list = [os.path.join(path, _file) for _file in os.listdir(folder_loc)]
            for index, filepath in enumerate(src_list):
                os.rename(filepath, dest_list[index])
            os.rmdir(folder_loc)
