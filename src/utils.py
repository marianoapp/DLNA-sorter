import os.path


def get_base_folder():
    base_path = os.path.dirname(__file__)
    if base_path.endswith(".pyz"):
        base_path = os.path.join(base_path, os.path.pardir)
    return os.path.abspath(base_path)
