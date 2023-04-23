from typing import List, Tuple

# options
DEFAULT_OUT_DIR = "iiif_output/"
# manifest params
##ImageList
Uri = str
Filename = str
ImageList = List[Tuple[Uri, Filename]]
##MetadataList
Label = str
Value = str
MetadataList = List[Tuple[Label, Value]]
