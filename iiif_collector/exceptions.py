import os


class FormatInvalidException(Exception):
    """Your file format is invalid. Accepted formats are only text/csv with extension .txt or .csv"""

    def __init__(self, file):
        self.file_name, self.file_extension = os.path.splitext("/Users/pankaj/abc.txt")
        super().__init__(f"The current file extension is {self.file_extension}")
