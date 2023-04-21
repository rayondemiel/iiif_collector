import click
import tqdm
import os
import requests

from scr.iiif import ManifestIIIF
from scr.utils import make_out_dirs

# test https://bvmm.irht.cnrs.fr/iiif/17495/manifest

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
