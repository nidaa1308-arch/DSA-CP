"""
Standardized API Error Hierarchy & Custom Exceptions.
"""

from fastapi import HTTPException, status


class BhumiException(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str, details: dict = None):
        super().__init__(
            status_code=status_code,
            detail={
                "error": error_code,
                "message": message,
                "details": details or {},
            }
        )


class InsufficientSourcesException(BhumiException):
    def __init__(self, message: str = "Required cadastral and building footprint layers are missing."):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="INSUFFICIENT_SOURCES",
            message=message
        )


class InvalidFileFormatException(BhumiException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_FILE_FORMAT",
            message=message,
            details=details
        )


class EntityNotFoundException(BhumiException):
    def __init__(self, entity_name: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ENTITY_NOT_FOUND",
            message=f"{entity_name} '{entity_id}' was not found."
        )


class AuditIntegrityException(BhumiException):
    def __init__(self, message: str, tampered_id: str = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="AUDIT_CHAIN_CORRUPTED",
            message=message,
            details={"tampered_at": tampered_id}
        )
