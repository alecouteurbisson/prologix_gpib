"""
Utility functions for Prologix GPIB operations.
"""

import re
from typing import List, Optional


def parse_scpi_response(response: str) -> dict:
    """
    Parse SCPI-style responses into a dictionary.
    
    Args:
        response: Raw SCPI response string
        
    Returns:
        Parsed data as dictionary
    """
    result = {}
    
    # Handle common patterns
    lines = response.strip().split('\n')
    
    for line in lines:
        if '=' in line:
            key, value = line.split('=', 1)
            result[key.strip()] = value.strip()
    
    return result


def parse_number(value: str) -> float:
    """
    Parse a string into a number (int or float).
    
    Args:
        value: String representation of a number
        
    Returns:
        Parsed number
    """
    try:
        if '.' in value or 'E' in value.upper():
            return float(value)
        return int(value)
    except ValueError:
        raise ValueError(f"Cannot parse '{value}' as number")


def format_scpi_command(command: str, parameters: Optional[List] = None) -> str:
    """
    Format an SCPI command with optional parameters.
    
    Args:
        command: Base SCPI command (e.g., "MEAS:VOLT")
        parameters: List of parameter values
        
    Returns:
        Formatted SCPI command
    """
    if not parameters:
        return command
    
    # Convert parameters to strings and join with commas
    param_str = ','.join(str(p) for p in parameters)
    return f"{command} {param_str}"


def validate_address(address: int, allow_sad: bool = False) -> None:
    """
    Validate a GPIB address.
    
    Args:
        address: Address to validate
        allow_sad: Whether secondary addresses are allowed
        
    Raises:
        ValueError: If address is invalid
    """
    if not isinstance(address, int):
        raise ValueError("Address must be an integer")
    
    if allow_sad:
        valid = (0 <= address <= 30) or (96 <= address <= 126)
    else:
        valid = 0 <= address <= 30
    
    if not valid:
        if allow_sad:
            raise ValueError(
                f"Address must be between 0-30 or 96-126, got {address}"
            )
        raise ValueError(f"GPIB address must be between 0-30, got {address}")


def escape_binary_data(data: bytes) -> bytes:
    """
    Escape special characters in binary data for transmission.
    
    Special characters that need escaping:
    - CR (13)
    - LF (10)
    - ESC (27)
    - '+' (43)
    
    Args:
        data: Raw binary data
        
    Returns:
        Escaped binary data
    """
    escaped = bytearray()
    
    for byte in data:
        if byte in (13, 10, 27, 43):
            # Escape with ESC character (27)
            escaped.append(27)
        escaped.append(byte)
    
    return bytes(escaped)


def unescape_binary_data(data: bytes) -> bytes:
    """
    Unescape special characters in received binary data.
    
    Args:
        data: Escaped binary data
        
    Returns:
        Unescaped binary data
    """
    result = bytearray()
    skip_next = False
    
    for i, byte in enumerate(data):
        if skip_next:
            skip_next = False
            continue
            
        if byte == 27 and i + 1 < len(data):
            # This is an escape sequence
            skip_next = True
            # Add the next character as-is (it was escaped)
            result.append(data[i + 1])
        else:
            result.append(byte)
    
    return bytes(result)


def parse_idn(idn_string: str) -> dict:
    """
    Parse instrument identification string.
    
    SCPI standard format: MANUFACTOR,MODEL,SERIAL,FIRMWARE
    
    Args:
        idn_string: Raw IDN response
        
    Returns:
        Dictionary with manufacturer, model, serial, firmware
    """
    parts = [p.strip() for p in idn_string.split(',')]
    
    result = {
        'manufacturer': parts[0] if len(parts) > 0 else '',
        'model': parts[1] if len(parts) > 1 else '',
        'serial': parts[2] if len(parts) > 2 else '',
        'firmware': parts[3] if len(parts) > 3 else ''
    }
    
    return result


def create_command_block(commands: List[str]) -> str:
    """
    Create a block of commands separated by semicolons.
    
    Args:
        commands: List of command strings
        
    Returns:
        Combined command string
    """
    return ';'.join(commands)
