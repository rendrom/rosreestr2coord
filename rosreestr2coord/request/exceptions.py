class RequestException(Exception):
    pass


class TimeoutException(RequestException):
    pass


class HTTPBadRequestException(RequestException):
    pass


class HTTPErrorException(RequestException):
    pass


class HTTPForbiddenException(RequestException):
    pass
