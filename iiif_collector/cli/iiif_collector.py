import click
import os
import logging
from requests import Session

from iiif_collector.exceptions import FormatInvalidException
from iiif_collector.iiif import ManifestIIIF, ImageIIIF
from iiif_collector.iiif_list import ListIIIF
from iiif_collector.opt.terminal import prompt
from iiif_collector.opt.utils import make_out_dirs, journal_error
from iiif_collector.variables import DEFAULT_OUT_DIR, DEFAULT_CSV
from iiif_collector.multiproc import ParallelizeIIIF


@click.group()
def run_collect():
    """CLI for collecting and downloading IIIF images, metadata, and manifests."""
    pass


@run_collect.command()
@click.argument("url", type=click.STRING)
@click.option("-i", "--image", "image", type=bool, default=False, is_flag=True, help="Active image api")
@click.option("-s", "--size", "size", type=str, default="max",
              help="Parameter to resize image. Basic resize is ',640' to change height for 640 px or '640,' to change "
                   "width. To more example, refer to image IIIF documentation.")
@click.option("-q", "--quality", "quality", type=click.Choice(['native', 'gray', 'bitonal', 'color']), default="native",
              help="To change quality parameter determines whether the image is delivered in color, grayscale or "
                   "black and white")
@click.option("-r", "--rotation", "rotation", type=int, default=0, help="Rotation parameter specifies mirroring and \
                                                                            rotation, 0 to 360.")
@click.option("-R", "--region", "region", type=str, default="full", help="The region parameter defines the rectangular \
                                                                            portion of the underlying image content to \
                                                                            be returned (x,y,w,h). Use [pct:x,y,w,h] to select point.\
                                                                             Default value is [full], [square] to \
                                                                             determine area where the width\
                                                                            and height are both equal.")
@click.option("-f", "--format", "format",
              type=click.Choice(['default', 'jpg', 'tif', 'png', 'gif', 'jp2', 'pdf', 'webp']),
              default="default", help="Select image format.")
@click.option("-a", "--api", "api", type=float, default=3.0, help="Determine API level to change change configuration")
@click.option("-d", "--directory", "directory", type=click.Path(exists=True, dir_okay=True, file_okay=False),
              default="./",
              help="Directory where to save the images")
@click.option("-n", "--number", "number", type=bool, is_flag=True,
              help="To active selection of images to save by manifest")
@click.option("--random", "random", type=bool, is_flag=True, help="To get randomize images according to the "
                                                                  "number indicated")
@click.option("--filename", "filename", type=bool, is_flag=True,
              help="To obtain a simplified image name (for manifests)")
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True, help="Get more verbosity")
def iiif_singular(url, **kwargs):
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
    current_path = os.getcwd()
    if kwargs['directory'] != "./":
        current_path = os.path.join(current_path, kwargs['directory'])

    # Selection mode
    if kwargs['image']:
        # Determine good path in case of singular image
        out_dir = os.path.join(current_path, DEFAULT_OUT_DIR, "API_IMAGE")
        # Instance image url
        image = ImageIIIF(url=str(url), path=out_dir, verbose=kwargs['verbose'])
        # create directory
        make_out_dirs(image.out_dir)
        journal_error(level='INFO', object=image.out_dir, message="Creating directory to IIIF files")
        if kwargs['verbose']:
            print("Creating directory to IIIF files")
        # Change api configuration
        if kwargs['api'] != 3.0:
            image.api_mode(kwargs['api'])
            journal_error(level='INFO', object='API', message=str(image.API))
        # API parameters
        image.image_configuration(region=kwargs['region'],
                                  size=kwargs['size'],
                                  rotation=kwargs['rotation'],
                                  quality=kwargs['quality'],
                                  format=kwargs['format']
                                  )
        # To get and download image
        image.load_image()
        image.save_image()

    else:
        # Session
        session = Session()
        # Instance manifest
        manifest = ManifestIIIF(str(url),
                                path=current_path,
                                session=session,
                                n=n,
                                verbose=kwargs['verbose'],
                                random=kwargs['random'],
                                short_filename=kwargs['filename'])
        if kwargs['api'] != 3.0:
            manifest.api_mode(kwargs['api'])
        manifest.image_configuration(region=kwargs['region'],
                                     size=kwargs['size'],
                                     rotation=kwargs['rotation'],
                                     quality=kwargs['quality'],
                                     format=kwargs['format'],
                                     )
        journal_error(level='INFO', object=manifest.out_dir, message="Creating directory to IIIF files")
        if kwargs['verbose']:
            print("Creating directory to IIIF files")
        make_out_dirs(manifest.out_dir)
        # Get manifest, metadata and images
        manifest.save_manifest()
        manifest.save_metadata()
        manifest.save_image()

    print("! Finish !")


@run_collect.command()
@click.argument("file", type=click.STRING)
@click.option("-i", "--image", "image", type=bool, default=False, is_flag=True, help="Active image api")
@click.option("-s", "--size", "size", type=str, default="max",
              help="Parameter to resize image. Basic resize is ',640' to change height for 640 px or '640,' to change "
                   "width. To more example, refer to image IIIF documentation.")
@click.option("-q", "--quality", "quality", type=click.Choice(['native', 'gray', 'bitonal', 'color']), default="native",
              help="Width to resize image")
@click.option("-r", "--rotation", "rotation", type=int, default=0, help="Rotation parameter specifies mirroring and \
                                                                            rotation, 0 to 360.")
@click.option("-R", "--region", "region", type=str, default="full", help="The region parameter defines the "
                                                                         "rectangular  portion of the underlying "
                                                                         "image content to  be returned (x,y,w,"
                                                                         "h). Use [pct:x,y,w,h] to select point. "
                                                                         "Default value is [full], [square] to  "
                                                                         "determine area where the width and height "
                                                                         "are both equal.")
@click.option("-f", "--format", "format",
              type=click.Choice(['default', 'jpg', 'tif', 'png', 'gif', 'jp2', 'pdf', 'webp']),
              default="default", help="Select image format.")
@click.option("-a", "--api", "api", type=float, default=3.0, help="Determine API level to change change configuration")
@click.option("-d", "--directory", "directory", type=click.Path(exists=True, dir_okay=True, file_okay=False),
              default="./",
              help="Directory where to save the images")
@click.option("-n", "--number", "number", type=bool, is_flag=True,
              help="To active selection of images to save by manifest")
@click.option("--random", "random", type=bool, is_flag=True, help="To get randomize images according to the "
                                                                  "number indicated")
@click.option("--case-insensitive", "case_insensitive", type=bool, is_flag=True,
              help="To disabled case sensitive for the name of your column (csv)")
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True, help="Get more verbosity")
@click.option("--filename", "filename", type=bool, is_flag=True,
              help="To obtain a simplified image name (for manifests)")
@click.option('--retry', 'retry', type=int, default=10,
              help="Option to readjust the number of tries for asynchronous requests. A large number of requests can "
                   "unnecessarily increase the process. The best practice is to test in the classic phase. If the "
                   "logs indicate a connection error, check whether the links work via your browser. If so, "
                   "increase accordingly.")
@click.option('--delay', 'delay', type=int, default=5,
              help="Option to readjust the delay between repetitions of asynchronous requests. Delaying a request may "
                   "unnecessarily increase the process. The best practice is to test in the classic phase. If the "
                   "logs indicate a connection error, check whether the links work via your browser. If so, "
                   "increase accordingly.")
def iiif_list(file, **kwargs):
    """
    Process multiple IIIF URLs from a file.
    FILE: Path to file containing IIIF URLs (TXT or CSV format).
    """
    # determinate quantity
    if kwargs['number']:
        n = int(input("How many images do you want (15 recommended)?"))
    else:
        # ALL
        n = None

    # Get path
    current_path = os.getcwd()
    if kwargs['directory'] != "./":
        current_path = os.path.join(current_path, kwargs['directory'])

    # Parsing file
    list_iiif = ListIIIF(case_insensitive=kwargs['case_insensitive'], verbose=kwargs['verbose'])
    # TXT
    if file.endswith('.txt'):
        try:
            list_iiif.read_txt(file)
            journal_error(level='INFO', object=file, message=f"Reading succeed")
        except Exception as err:
            journal_error(level='ERROR', object=file, message=str(err))
    # CSV
    elif file.endswith('.csv'):
        name_column = str(input("What is the name of iiif columns ? "))
        print("Parameters by default :")
        print(f"delimiter : {DEFAULT_CSV[0]}")
        print(f"header : {DEFAULT_CSV[1]}")
        print(f"encoding: {DEFAULT_CSV[2]}")
        journal_error(level='INFO', object='Config csv reader', message=f"Parameters by default : delimiter : {DEFAULT_CSV[0]}, \
                        header : {DEFAULT_CSV[1]}, encoding: {DEFAULT_CSV[2]}")
        delimiter, header, encoding = prompt()
        try:
            list_iiif.read_csv(file, name_column, delimiter=delimiter.strip(), encoding=encoding.lower().strip(),
                               header=int(header))
        except KeyError as err:
            journal_error(level='ERROR', object=file, message=str(err),
                          complement_info='Impossible to find the column. Please '
                                          'retake yours informations.')
            print('Impossible to find the column. Please retake yours informations.')
    # Invalid format
    else:
        journal_error(level='ERROR', object=file, message=str(FileExistsError),
                      complement_info="Sorry, your file need to be in csv or txt format.")
        raise FormatInvalidException(file)

    if kwargs['image']:
        parallelization = ParallelizeIIIF(urls=list_iiif.url_iiif,
                                          path=current_path,
                                          image=True,
                                          retry=kwargs['retry'],
                                          delay=kwargs['delay'],
                                          verbose=kwargs['verbose'])
        # API parameters
        parallelization.image_configuration(region=kwargs['region'],
                                            size=kwargs['size'],
                                            rotation=kwargs['rotation'],
                                            quality=kwargs['quality'],
                                            format=kwargs['format'])
        make_out_dirs(parallelization.out_dir, api=True)
        parallelization.run()
    else:
        parallelization = ParallelizeIIIF(urls=list_iiif.url_iiif,
                                          path=current_path,
                                          verbose=kwargs['verbose'],
                                          retry=kwargs['retry'],
                                          delay=kwargs['delay'],
                                          n=n,
                                          random=kwargs['random'],
                                          short_filename=kwargs['filename'])
        # API parameters
        parallelization.image_configuration(region=kwargs['region'],
                                            size=kwargs['size'],
                                            rotation=kwargs['rotation'],
                                            quality=kwargs['quality'],
                                            format=kwargs['format'])
        parallelization.run()


@run_collect.command()
@click.argument("url", type=click.STRING)
@click.option("-d", "--directory", "directory", type=click.Path(exists=True, dir_okay=True, file_okay=False),
              default="./",
              help="Directory where to save the images")
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True, help="Get more verbosity")
def get_list_image(url, **kwargs):
    """
    Retrieve and save a list of images from a IIIF manifest.

    URL: IIIF manifest URL.
    """
    journal_error(level='INFO', object='', message="############### Start collect get_list_image ###############")
    # Get path
    current_path = os.getcwd()
    if kwargs['directory'] != "./":
        current_path = os.path.join(current_path, kwargs['directory'])

    manifest = ManifestIIIF(str(url), path=current_path, verbose=kwargs['verbose'])
    make_out_dirs(manifest.out_dir)

    manifest.save_list_images()
    manifest.save_metadata()
    manifest.save_manifest()

    journal_error(level='INFO', object='',
                  message=f"""You can find the file at the following path : <{manifest.__print_path__('images')}>""")
    journal_error(level='INFO', object='', message="############### Process collect get_list_image ending "
                                                   "###############")
    print("Process collect get_list_image ending")
    print(f"""You can find the file at the following path : <{manifest.__print_path__('images')}>""")


if __name__ == "__main__":
    logging.basicConfig(filename='output/logfile.txt', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    run_collect()
