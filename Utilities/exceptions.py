from time import asctime
"""
Custom exceptions for Chroma Automation Suite.
"""

class ChromaError(Exception):
    """ Base error for all others. Captures module information. """

    def __init__(self, message, module):
        """
        Constructs a ChromaError.

        :param message: Error message to display.
        :param module: module where error occured.
        :return:
        """
        super(ChromaError, self).__init__()
        self.msg = message
        self.module = module


    def __str__(self):
        """ Return error message. """
        return "{} @ {} in {}".format(str(self.msg), asctime(), self.module)


class InvalidSideError(ChromaError):
    """
    If an invalid side is selected for some reason. Returns the bad
    value.
    """
    def __init__(self, module, side):
        """
        Construct an invalid side error. Kinda self-expalantory, meant for
        when an invalid side paramter (not 0 or 1) is passed.

        :param module: Module where error occured
        :param side: Invalid parameter
        :return: An InvalidSideError
        """
        super(InvalidSideError, self).__init__()
        self.module = module
        self.side = side
        self.msg = "Bad Side: {}".format(self.side)


class InvalidUserError(ChromaError):
    """
    If an invalid user is selected for some reason. Returns an error
    with the invalid username.
    """
    def __init__(self, module, username):
        """
        Construct an InvalidUserError. Meant for when an invalid username
        is passed somewhere. Probably a username looked up in the database
        that hasn't been entered yet.

        :param module: Module where the error was raised
        :param username: Invalid username passed
        :return: An InvalidUserError
        """
        super(InvalidUserError, self).__init__()
        self.module = module
        self.username = username
        self.msg = "Bad Username: {}".format(self.username)