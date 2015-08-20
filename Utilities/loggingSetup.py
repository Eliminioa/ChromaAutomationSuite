import os
import logging

__author__ = 'Eliminioa'
__version__ = 'v 3.03'

LOGGING_ON = False
HOME_DIRECTORY = '/app'

def create_logger(name):
    # noinspection PyUnusedLocal
    dir_path = os.path.abspath(os.curdir)
    log_filename = HOME_DIRECTORY + '/Utilities/PrimeLog.log'
    log = logging.getLogger(name)

    if LOGGING_ON:
        fhdlr = logging.FileHandler(log_filename, 'w')
    else:
        fhdlr = logging.StreamHandler()
    log.setLevel(logging.DEBUG)

    fmtr = logging.Formatter('%(levelname)s in %(name)s: %(message)s @ %(asctime)s')
    fhdlr.setFormatter(fmtr)
    fhdlr.setLevel(logging.DEBUG)
    log.addHandler(fhdlr)
    log.debug('Logger online!')

    return log
