from typing import List, Tuple

# options
DEFAULT_OUT_DIR = "iiif_output/"

CONFIG_FOLDER = ['manifests', 'images', 'metadata']
OUTPUT_LIST_TXT = 'list_image.txt'

DEFAULT_CSV = (";", 0, "utf-8")

# manifest params
##ImageList
Uri = str
Filename = str
ImageList = List[Tuple[Uri, Filename]]
##MetadataList
Label = str
Value = str
MetadataList = List[Tuple[Label, Value]]
