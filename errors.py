# coding=utf-8


class AlfeConnectionError(Exception):
    """
    Exception raised when connection to server fails
    """
    pass

class AlfeFunctionCallError(Exception):
    """
    Exception raised when function call fails
    """
    def __init__(self, *args, **kwargs):
        super(AlfeFunctionCallError, self).__init__(*args, **kwargs)
        self.original_exception = None
