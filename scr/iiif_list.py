import pandas as pd


class ListIIIF:
    url_iiif = []
    len_iiif = 0

    def __len__(self):
        return len(self.url_iiif)

    def read_csv(self, file: str, column_name: str, **kwargs):
        df = pd.read_csv(file, **kwargs)
        column = df[[column_name]]
        column = column.dropna()
        for item in column.values.tolist():
            self.url_iiif.append(item[0])
            self.len_iiif = len(self.url_iiif)

    def read_txt(self, file):
        with open(file, mode='r') as f:
            txt = f.read()
            self.url_iiif = txt.split('\n')
            self.len_iiif = len(self.url_iiif)

    def __get_next__(self):
        return next(iter(self.url_iiif))
