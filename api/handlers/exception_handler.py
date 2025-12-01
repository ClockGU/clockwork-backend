from fastapi import HTTPException
from typing import Optional


class ExceptionHandler:
    """Centralized exception handler for consistent error responses across the application"""
    
    @staticmethod
    def not_found(resource: str, identifier: Optional[str] = None, message: Optional[str] = None) -> HTTPException:
        """
        Raise 404 Not Found exception
        
        Args:
            resource: Name of the resource (e.g., "Petition", "Employee")
            identifier: ID or identifier of the resource
            message: Custom message (overrides default)
        """
        if message:
            detail = message
        elif identifier:
            detail = f"{resource} with ID {identifier} not found"
        else:
            detail = f"{resource} not found"
        
        return HTTPException(status_code=404, detail=detail)
    
    @staticmethod
    def bad_request(message: str = "Bad request") -> HTTPException:
        """
        Raise 400 Bad Request exception
        
        Args:
            message: Error message describing what went wrong
        """
        return HTTPException(status_code=400, detail=message)
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> HTTPException:
        """
        Raise 401 Unauthorized exception
        
        Args:
            message: Error message about authentication
        """
        return HTTPException(status_code=401, detail=message)
    
    @staticmethod
    def forbidden(message: str = "You don't have permission to perform this action") -> HTTPException:
        """
        Raise 403 Forbidden exception
        
        Args:
            message: Error message about permissions
        """
        return HTTPException(status_code=403, detail=message)
    
    @staticmethod
    def conflict(message: str = "Resource conflict") -> HTTPException:
        """
        Raise 409 Conflict exception
        
        Args:
            message: Error message about the conflict
        """
        return HTTPException(status_code=409, detail=message)
    
    @staticmethod
    def unprocessable_entity(message: str = "Unprocessable entity") -> HTTPException:
        """
        Raise 422 Unprocessable Entity exception
        
        Args:
            message: Error message about validation failure
        """
        return HTTPException(status_code=422, detail=message)
    
    @staticmethod
    def internal_error(operation: Optional[str] = None, error: Optional[Exception] = None, message: Optional[str] = None) -> HTTPException:
        """
        Raise 500 Internal Server Error exception
        
        Args:
            operation: Description of what operation failed (e.g., "creating petition")
            error: The underlying exception
            message: Custom message (overrides default)
        """
        if message:
            detail = message
        elif operation and error:
            detail = f"An error occurred while {operation}: {str(error)}"
        elif operation:
            detail = f"An error occurred while {operation}"
        elif error:
            detail = f"An error occurred: {str(error)}"
        else:
            detail = "An internal server error occurred"
        
        return HTTPException(status_code=500, detail=detail)
    
    @staticmethod
    def created_failed(resource: str, message: Optional[str] = None) -> HTTPException:
        """
        Raise 400 exception when resource creation fails
        
        Args:
            resource: Name of the resource that failed to create
            message: Custom message (overrides default)
        """
        if message:
            detail = message
        else:
            detail = f"{resource} could not be created"
        
        return HTTPException(status_code=400, detail=detail)
    
    @staticmethod
    def update_failed(resource: str, identifier: Optional[str] = None, message: Optional[str] = None) -> HTTPException:
        """
        Raise 400 exception when resource update fails
        
        Args:
            resource: Name of the resource that failed to update
            identifier: ID of the resource
            message: Custom message (overrides default)
        """
        if message:
            detail = message
        elif identifier:
            detail = f"{resource} with ID {identifier} could not be updated"
        else:
            detail = f"{resource} could not be updated"
        
        return HTTPException(status_code=400, detail=detail)
    
    @staticmethod
    def delete_failed(resource: str, identifier: Optional[str] = None, message: Optional[str] = None) -> HTTPException:
        """
        Raise 400 exception when resource deletion fails
        
        Args:
            resource: Name of the resource that failed to delete
            identifier: ID of the resource
            message: Custom message (overrides default)
        """
        if message:
            detail = message
        elif identifier:
            detail = f"{resource} with ID {identifier} could not be deleted"
        else:
            detail = f"{resource} could not be deleted"
        
        return HTTPException(status_code=400, detail=detail)
    
    @staticmethod
    def invalid_status(current_status: str, required_status: Optional[str] = None, message: Optional[str] = None) -> HTTPException:
        """
        Raise 400 exception for invalid status transitions
        
        Args:
            current_status: Current status of the resource
            required_status: Required status for the operation
            message: Custom message (overrides default)
        """
        if message:
            detail = message
        elif required_status:
            detail = f"Invalid status. Current status is '{current_status}', but must be '{required_status}' for this operation"
        else:
            detail = f"Invalid status: '{current_status}'"
        
        return HTTPException(status_code=400, detail=detail)
    
    @staticmethod
    def custom(status_code: int, message: str) -> HTTPException:
        """
        Raise custom HTTP exception
        
        Args:
            status_code: HTTP status code
            message: Error message
        """
        return HTTPException(status_code=status_code, detail=message)
