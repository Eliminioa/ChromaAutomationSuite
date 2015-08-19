import os
import logging

__author__ = 'Eliminioa'
__version__ = 'v 3.03'

LOGGING_ON = True
HOME_DIRECTORY = '/app'

def create_logger(name):
    # noinspection PyUnusedLocal
    dir_path = os.path.abspath(os.curdir)
    log_filename = HOME_DIRECTORY + '/Utilities/PrimeLog.log'

    if LOGGING_ON:
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)

        fhdlr = logging.FileHandler(log_filename, 'a')
        fmtr = logging.Formatter('%(levelname)s in %(name)s: %(message)s @ %(asctime)s')
        fhdlr.setFormatter(fmtr)
        fhdlr.setLevel(logging.DEBUG)
        log.addHandler(fhdlr)
        log.debug('Logger online!')

    else:
        log = null_logger('NULL')

    return log

class null_logger(logging.Logger):

    def _log(self, level, msg, args, exc_info=None, extra=None):
        pass