"""Exceptions for IntesisHome Local"""


class IntesisHomeException(Exception):
    """Base exception of the IntesisHome client"""


class IntesisHomeUnauthenticatedException(IntesisHomeException):
    """An attempt is made to perform a request which requires
    authentication while the client is not authenticated."""


class IntesisHomeAuthenticationFailedException(IntesisHomeException):
    """An attempt to authenticate failed."""
