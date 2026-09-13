"""UUID utility functions for consistent handling across services."""
import uuid
from typing import Optional, Union


def to_uuid(value: Optional[Union[str, uuid.UUID]]) -> Optional[uuid.UUID]:
    """Convert string or UUID to UUID type.
    
    Args:
        value: String or UUID value
        
    Returns:
        UUID object or None if input is None
    """
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        return uuid.UUID(value)
    raise TypeError(f"Cannot convert {type(value)} to UUID")
