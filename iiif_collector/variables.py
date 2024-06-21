from typing import List, Tuple

# options
DEFAULT_OUT_DIR = "iiif_output"

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

# TESTS
TEST_IIIF_MANIFEST = {
    "@context": "http://iiif.io/api/presentation/2/context.json",
    "@id": "https://example.org/iiif/book1/manifest",
    "@type": "sc:Manifest",
    "label": "Sample Book",
    "metadata": [
        {
            "label": "Author",
            "value": "John Doe"
        },
        {
            "label": "Published",
            "value": "2023"
        }
    ],
    "sequences": [
        {
            "@id": "https://example.org/iiif/book1/sequence/normal",
            "@type": "sc:Sequence",
            "canvases": [
                {
                    "@id": "https://example.org/iiif/book1/canvas/p1",
                    "@type": "sc:Canvas",
                    "label": "Page 1",
                    "height": 1800,
                    "width": 1200,
                    "images": [
                        {
                            "@id": "https://example.org/iiif/book1/annotation/p0001-image",
                            "@type": "oa:Annotation",
                            "motivation": "sc:painting",
                            "resource": {
                                "@id": "https://example.org/iiif/book1/res/page1/full/full/0/default.jpg",
                                "@type": "dctypes:Image",
                                "format": "image/jpeg",
                                "height": 1800,
                                "width": 1200
                            },
                            "on": "https://example.org/iiif/book1/canvas/p1"
                        }
                    ]
                }
            ]
        }
    ]
}
