import os
import sys


def add_local_component_libs_to_sys_path():
    sys.path.insert(0, os.path.dirname(__file__) + '/../../')
    sys.path.insert(0, os.path.dirname(__file__) + '/../../../api')


def get_data_file_path(filename):
    return os.path.join(os.path.dirname(__file__), 'test_data', filename)

