import os
import json
from PIL import Image, ImageTk
import io
import binascii

def load_fixture(filename: str):
    file_path = os.path.join(os.path.dirname(__file__), r'fixtures', filename)
    extension = os.path.splitext(file_path)[1]
    with open(file_path, 'r', encoding='utf-8') as file:
        if extension == 'json':
            return json.read(file)
        else:
            return file.read()
        
def resize_image_with_width(image, width):
        image_width, image_height = image.size
        image_ratio = image_width / image_height
        new_image_width = width
        new_image_height = int(new_image_width / image_ratio)

        image = image.resize((new_image_width, new_image_height))
        return image

def prepare_image(image_data, width):
    image = Image.open(io.BytesIO(binascii.unhexlify(image_data)))
    image = resize_image_with_width(image, width)
    image = ImageTk.PhotoImage(image)
    return image