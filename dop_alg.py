import zipfile
import cv2
import os
import tempfile
import imghdr
import shutil
from werkzeug.datastructures import FileStorage


def extract_and_read_images(file_storage: FileStorage):
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, 'archive.zip')
        file_storage.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        images = []

        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if imghdr.what(file_path):
                    image = cv2.imread(file_path)
                    if image is not None:
                        images.append(image)
        return images


def clean(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass