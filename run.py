import click
import os

from scr.iiif import ManifestIIIF, ImageIIIF
from scr.utils import make_out_dirs


# test https://bvmm.irht.cnrs.fr/iiif/17495/manifest
# test2 https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb10402127/manifest   -> voir pour telecharger sortie ocr (seealso)
# retourne lien html (https://github.com/kba/hocr-spec)
# ref 1 https://github.com/PonteIneptique/iiif-random-downloader/blob/main/cli.py
# ref 2 https://github.com/YaleDHLab/iiif-downloader/blob/master/iiif_downloader/__init__.py#L16


@click.command()
@click.argument("url", type=click.STRING)
@click.option("-i", "--image", "image", type=bool, default=False, is_flag=True, help="Active image api")
@click.option("-w", "--width", "width", type=str, default="max", help="Width to resize image")
@click.option("-q", "--quality", "quality", type=click.Choice(['native', 'gray', 'bitonal', 'color']), default="native",
              help="Width to resize image")
@click.option("-r", "--rotation", "rotation", type=int, default=0, help="Rotation parameter specifies mirroring and \
                                                                            rotation, 0 to 360.")
@click.option("-R", "--region", "region", type=str, default="full", help="The region parameter defines the rectangular \
                                                                            portion of the underlying image content to \
                                                                            be returned (x,y,w,h). Use [pct:x,y,w,h] to select point.\
                                                                             Default value is [full], [square] to \
                                                                             determine area where the width\
                                                                            and height are both equal.")
@click.option("-f", "--format", "format", type=click.Choice(['jpg', 'tif', 'png', 'gif', 'jp2', 'pdf', 'webp']),
              default='jpg', help="Select image format.")
@click.option("-a", "--api", "api", type=float, default=3.0, help="Determine API level to change change configuration")
@click.option("-d", "--directory", "directory", type=click.Path(exists=True, dir_okay=True, file_okay=False),
              default="./",
              help="Directory where to save the images")
@click.option("-n", "--number", "number", type=bool, is_flag=True,
              help="To active selection of images to save by manifest")
@click.option("--random", "random", type=bool, is_flag=True, help="To get randomize images according to the "
                                                                  "number indicated")
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True, help="Get more verbosity")
def run_collect(url, **kwargs):
    """
    Running script to get and download iiif images, metadata and manifests. If you want access to specific image IIIF,
    you must activate the option.

    :param url: url IIIF manifest or images
    """

    # determinate quantity
    if kwargs['number']:
        n = int(input("How many images do you want (15 recommended)?"))
    else:
        # ALL
        n = None

    # Get path
    current_path = os.path.dirname(os.path.abspath(__file__))
    if kwargs['directory'] != "./":
        current_path = os.path.join(current_path, kwargs['directory'])

    # Selection mode
    if kwargs['image']:
        image = ImageIIIF(url=str(url), path=current_path, verbose=kwargs['verbose'])
        if kwargs['api'] != 3.0:
            image.api_mode(kwargs['api'])
        image.image_configuration(region=kwargs['region'],
                                  size=kwargs['width'],
                                  rotation=kwargs['rotation'],
                                  quality=kwargs['quality'],
                                  format=kwargs['format'],
                                  )
        print(image.API)
        print(image.config)
    else:
        manifest = ManifestIIIF(str(url), path=current_path, n=n,
                                verbose=kwargs['verbose'], random=kwargs['random'],
                                )
        if kwargs['verbose']:
            print("Creating directory to IIIF files")
        make_out_dirs(manifest.out_dir)
        manifest.save_manifest()
        manifest.save_metadata()
        manifest.save_image()

    print("! Finish !")


if __name__ == "__main__":
    run_collect()
