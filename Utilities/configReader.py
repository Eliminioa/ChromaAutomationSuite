import os
import re
import json
from loggingSetup import create_logger


__author__ = 'Eliminioa'

class ConfigReader(object):

    def __init__(self, side=None):
        """
        This is what grabs all the config info. Should be referenced only in
        connector.py, and passed on from there.

        :param side: Which side to load the config data of.
        :return: A ConfigReader object that contains all necessary
                configuration information.
        """
        self.log = create_logger(__name__)

        if side not in ['periwinkle', 'orangered', None]:
            side = None
        self.side = side
        self.log.debug('Got info for %(side)s' % {'side': side})

        script_directory = re.sub('\\\\\w+$', '', os.getcwd())
        global_cfg_filename = '\Config\global_config.json'
        if side == 'periwinkle':
            config_filename = 'periwinkle_config'
        elif side == 'orangered':
            config_filename = 'orangered_config'
        else:
            config_filename = 'global_config'
        local_cfg_filename = ('\Config\%(filename)s.json' %
                              {'filename': config_filename}
                              )

        self.log.debug('''Global config file is %(global_file)s
                       Local config file is %(local_file)s''' %
                       {"global_file": global_cfg_filename,
                        "local_file": local_cfg_filename}
                       )

        # Get global config settings
        try:
            with open(script_directory + global_cfg_filename, 'r') as config_file:
                global_config_info = json.load(config_file)
            for item in global_config_info.keys():
                exec 'self._%(varName)s = global_config_info[%(varName)r]' %\
                     {'varName': item}
        except IOError as e:
            self.log.exception('Bad config filename: %(cfg_filename)s' %
                               {'cfg_filename': global_cfg_filename}
                               )
            raise e

        # Get local config settings
        try:
            with open(script_directory + local_cfg_filename, 'r') as config_file:
                local_config_info = json.load(config_file)
            for item in local_config_info.keys():
                exec "self.%(varName)s = local_config_info[%(varName)r]" %\
                     {"varName": item}
        except IOError as e:
            self.log.exception('Bad config filename: %(cfg_filename)s' %
                               {'cfg_filename': local_cfg_filename}
                               )
            raise e

    def save(self):
        # find the local config file
        script_directory = re.sub('\\\\\w+$', '', os.getcwd())
        if self.side == 'periwinkle':
            config_filename = 'periwinkle_config'
        elif self.side == 'orangered':
            config_filename = 'orangered_config'
        else:
            config_filename = 'periwinkle_config'
        local_cfg_filename = ('\Config\%(filename)s.json' %
                              {'filename': config_filename}
                              )
        # get the values stored in the local config
        with open(script_directory + local_cfg_filename, 'r') as config_file:
            keys = json.load(config_file).keys()

        # generate a dictionary of local config variables and their values
        vars_dict = {}
        for key in keys:
            vars_dict[key] = eval('self.%(var)s' % {'var': key},
                                  globals(), locals()
                                  )

        # dump this dictionary into the local config file
        with open(script_directory + local_cfg_filename, 'w') as config_file:
            json.dump(vars_dict, config_file, indent=4)