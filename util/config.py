from configparser import ConfigParser
from os.path import dirname, join, abspath

class Config:
    def __init__(self, config_file):
        parser = ConfigParser()
        util_dir = dirname(abspath(__file__))
        parser.read(util_dir + f'/../config/{config_file}')
        self.parser = parser

    def get_section_conf(self, section) -> dict:
        items = self.parser.items(section)
        conf = {}
        for item in items:
            conf[item[0]] = item[1]
        return conf


config = Config('config.ini')

print(config.get_section_conf('notion'))