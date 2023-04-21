import click
import tqdm
import os

DEFAULT_OUT_DIR =


@click.command()
@click.argument("manifest", type=click.STRING, help="")
@click.option("--directory", type=click.Path(exists=True, dir_okay=True, file_okay=False), default="./",
              help="Directory where to save the images")
@click.option("--number", type=int, help="Number of images to save", default=10)
def run_collect():
    return None


if __name__ == "__main__":
    run_collect()
