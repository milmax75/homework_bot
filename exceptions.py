class APINotRespondedException(Exception):
    '''API not responded'''
    pass


class APIUnavailableException(Exception):
    '''API not available'''
    pass


class NotDictError(Exception):
    '''Dictionary not received'''
    pass


class HomeworkStatusError(Exception):
    '''Unknown homework status'''
    pass

class HomeworkDataError(Exception):
    '''Data received cant be parsed'''
    pass

class TokensValidationError(Exception):
    '''Tokens cant be validated'''
    pass
