import os
import sys


def add_local_component_libs_to_sys_path():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../api'))


def get_data_file_path(filename):
    return os.path.join(os.path.dirname(__file__), 'test_data', filename)


def is_all_same_color(image, color_tuple):
    return (image == color_tuple).all()


def is_all_black(image):
    return is_all_same_color(image, (0, 0, 0))


def is_all_white(image):
    return is_all_same_color(image, (255, 255, 255))