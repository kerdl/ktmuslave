class BackendError(BaseException):
    ...

class FrontendError(BaseException):
    ...


""" ## Backend errors """
class NoSpaceSpecified(BackendError): ...
class NoContext(BackendError): ...
class NoMentionString(BackendError): ...
class NoEverythingWithDebugOn(BackendError): ...
class GoingToIgnoredState(BackendError): ...
