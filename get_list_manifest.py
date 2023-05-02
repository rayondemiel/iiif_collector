import click
import os

from scr.iiif import ManifestIIIF
from scr.utils import make_out_dirs


@click.command()
@click.argument("url", type=click.STRING)
@click.option("-d", "--directory", "directory", type=click.Path(exists=True, dir_okay=True, file_okay=False),
              default="./",
              help="Directory where to save the images")
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True, help="Get more verbosity")
def get_list_image(url, **kwargs):
    """
    Function to get a list of images url's
    :param url: link manifest IIIF
    :param directory: Path of select directory to store files. [DEFAULT = ./ ]
    :return: txt file with all url
    """
    # Get path
    current_path = os.path.dirname(os.path.abspath(__file__))
    if kwargs['directory'] != "./":
        current_path = os.path.join(current_path, kwargs['directory'])

    manifest = ManifestIIIF(str(url), path=current_path, verbose=kwargs['verbose'])
    make_out_dirs(manifest.out_dir)

    manifest.save_list_images()
    manifest.save_metadata()
    manifest.save_manifest()

    print("Finish")
    print(f"""You can find the file at the following path : <{manifest.__print_path__('images')}>""")


if __name__ == "__main__":
    get_list_image()
