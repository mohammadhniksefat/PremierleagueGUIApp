import os
import json

def load_fixture(filename: str):
    file_path = os.path.join(os.path.dirname(__file__), r'fixtures', filename)
    extension = os.path.splitext(file_path)[1]
    with open(file_path, 'r', encoding='utf-8') as file:
        if extension == 'json':
            return json.read(file)
        else:
            return file.read()