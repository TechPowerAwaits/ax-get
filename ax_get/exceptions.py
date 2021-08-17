# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD


class AxGetException(Exception):
    pass


class DirNotExistError(AxGetException):
    def __init__(self, filepath):
        self.message = f"The directory {filepath} does not exist"
        super().__init__(self.message)


class DirNotAccessibleError(AxGetException):
    def __init__(self, filepath):
        self.message = f"The directory {filepath} does exist, but can't be accessed"
        super().__init__(self.message)


class NotFileError(AxGetException):
    def __init__(self, filepath):
        self.message = f"The path {filepath} exists, but is not a regular file"
        super().__init__(self.message)


class InvalidBrandFile(AxGetException):
    def __init__(self, filepath):
        self.message = f"The provided brand file {filepath} is not valid"
        super().__init__(self.message)


class FileAlreadyExists(AxGetException):
    def __init__(self, filepath):
        self.message = f"The file {filepath} already exists"
        super().__init__(self.message)
