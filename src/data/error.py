from dataclasses import dataclass


class BackendError(BaseException):
    ...

class FrontendError(BaseException):
    ...


""" ## Backend errors """
class ZoomNameInDatabase(BackendError): ...
class ZoomNameNotInDatabase(BackendError): ...

@dataclass
class InvalidStatusCode(BackendError): 
    code: int