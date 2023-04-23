import os
import shutil
import json
import random

from .variables import ImageList, MetadataList


def cleaning_folder(path):
    """
    action to clean the describe folder
    :param path:
    :return: None
    """
    for filename in os.listdir(path):
        if filename != "readme.md":
            file_path = os.path.join(path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


def save_json(iiif_json: dict, file_path: str, ):
    """
    Save self.json to disk
    iiif_json : Dict, manifest IIIF
    file_path : str, directory to save json files
    """
    try:
        with open(os.path.join(file_path, "manifest_IIIF.json"), mode="w") as f:
            json.dump(iiif_json, f, indent=3, ensure_ascii=False)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))


def save_txt(list_mtda: MetadataList, file_path):
    try:
        with open(os.path.join(file_path, "metadata.txt"), 'w') as outfile:
            outfile.writelines((str(f"{i[0]} : {i[1]}") + '\n' for i in list_mtda))
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))


def make_out_dirs(path):
    """Make the output directories in which saved data is stored"""
    for d in ['manifests', 'images', 'metadata']:
        out_dir = os.path.join(path, d)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)


def randomized(image_list: ImageList, number: int = 10) -> ImageList:
    """ Selects [number] images from ImageList

    :param image_list: List of images link and filename
    :param number: Number of images to select
    :return: Filtered image list
    """
    # In place randomization
    random.shuffle(image_list)
    return image_list[:min(number, len(image_list) - 1)]
