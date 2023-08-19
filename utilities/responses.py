from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException



class SuccessResponse(JSONResponse):
    def __init__(self, message = None, data = None, status_code = 200):
        return super().__init__(
            content={
                "status": True,
                "message": message,
                "data": data
            },
            status_code=status_code
        )

class ErrorResponse(HTTPException):
    def __init__(self, message, data = None, status_code = 400):
        return super().__init__(
            detail={
                "status": False,
                "message": message,
                "data": data
            },
            status_code=status_code
        )