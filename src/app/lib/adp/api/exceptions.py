

class APIConnectionError(Exception):
    """Raised when an ADP API connection error occurs."""
    pass


class APIDisconnectionError(Exception):
    """Raised when an ADP API disconnection error occurs."""
    pass


class APIRequestDone(Exception):
    """Raised when an ADP API get request cursor reaches the end."""
    pass


class APIRequestError(Exception):
    """Raised when an ADP API get error occurs."""
    pass
