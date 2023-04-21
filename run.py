import click
import tqdm
import os
import requests

from scr.iiif import ManifestIIIF
from scr.utils import make_out_dirs

# test https://bvmm.irht.cnrs.fr/iiif/17495/manifest
#ref 1 https://github.com/PonteIneptique/iiif-random-downloader/blob/main/cli.py
# ref 2 https://github.com/YaleDHLab/iiif-downloader/blob/master/iiif_downloader/__init__.py#L16


@click.command()
@click.argument("url", type=click.STRING)
@click.option("--directory", type=click.Path(exists=True, dir_okay=True, file_okay=False), default="./",
              help="Directory where to save the images")
@click.option("--number", type=int, help="Number of images to save", default=10)
def run_collect(url, directory, number):

    os.path

    manifest = ManifestIIIF(str(url))


if __name__ == "__main__":
    run_collect()
