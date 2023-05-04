from typing import List, Tuple

# options
DEFAULT_OUT_DIR = "iiif_output/"

CONFIG_FOLDER = ['manifests', 'images', 'metadata']

# manifest params
##ImageList
Uri = str
Filename = str
ImageList = List[Tuple[Uri, Filename]]
##MetadataList
Label = str
Value = str
MetadataList = List[Tuple[Label, Value]]
