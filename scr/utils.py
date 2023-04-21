import os
import shutil


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


def save_json(obj, **kwargs):
    """Save self.json to disk"""
    with open(os.path.join(XML_CLEAN, "list_correction.json"), mode="w") as f:
        json.dump(list_files, f, indent=3, ensure_ascii=False)


def make_out_dirs(self):
    """Make the output directories in which saved data is stored"""
    for i in ['manifests', 'images', 'metadata']:
        out_dir = os.path.join(self.out_dir, i)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
