ERROR_OBJECT_NOT_FOUND = 10001
PARAMETER_REQUIRED = 10002
INVALID_IMAGE_FILE = 10003

class ImsException(BaseException):
    def __init__(self, error_code, error_msg):
        self.error_code = error_code
        self.error_msg = error_msg


class InvalidImageFile(ImsException):
    def __init__(self):
        super(InvalidImageFile, self).__init__(INVALID_IMAGE_FILE,
                                               'Invalid Image File')