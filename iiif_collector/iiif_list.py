import pandas as pd


class ListIIIF(object):
    """ A class for managing lists of IIIF URLs from different sources."""
    url_iiif = []
    len_iiif = 0

    def __init__(self, **kwargs):
        """
        Initializes a ListIIIF object.

        Args:
            verbose (bool): Optional. Set to True for verbose output.
            case_insensitive (bool): Optional. Set to True to make column names case insensitive.
        """
        self.verbose = kwargs.get('verbose', False)
        self.case = kwargs.get('case_insensitive', False)
    def __len__(self):
        """
        Returns the number of IIIF URLs currently stored.
        """
        return len(self.url_iiif)

    def read_csv(self, file: str, column_name: str, **kwargs):
        """
                Reads IIIF URLs from a CSV file and stores them in url_iiif.

                Args:
                    file (str): Path to the CSV file.
                    column_name (str): Name of the column containing IIIF URLs.
                    **kwargs: Additional keyword arguments passed to pandas.read_csv().

                Raises:
                    KeyError: If the specified column_name is not found (case sensitive).

                Notes:
                    If case_insensitive=True was set during initialization,
                    column names are treated as case insensitive.
        """
        df = pd.read_csv(file, **kwargs)
        if self.case:
            df.columns = df.columns.str.lower()
            column_name = column_name.lower()
        try:
            column = df[[column_name]]
        except KeyError:
            raise KeyError('Impossible to find the column. Please verify the name of your column. You can disabel case sensitive with [--case-insensitive] parameters.')
        column = column.dropna()
        for item in column.values.tolist():
            self.url_iiif.append(item[0])
            self.len_iiif = len(self.url_iiif)

    def read_txt(self, file: str):
        """
                Reads IIIF URLs from a text file and stores them in url_iiif.

                Args:
                    file (str): Path to the text file.
        """
        with open(file, mode='r') as f:
            txt = f.read()
            self.url_iiif = txt.split('\n')
            self.len_iiif = len(self.url_iiif)

    def __get_next__(self):
        """
                Returns the next IIIF URL from the stored list.

                Returns:
                    str: Next IIIF URL.
        """
        return next(iter(self.url_iiif))
