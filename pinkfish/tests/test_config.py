import os
import pinkfish as pf


def get_test_config_path(*args):
    ''' Returns the path to a .pinkfish config file
        in the tests directory.
    '''
    dire_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dire_path, ".pinkfish")
    return file_path

def read_config_for_tests():
    conf = {}
    conf["base_dir"] = os.path.dirname(os.path.abspath(__file__))
    return conf
