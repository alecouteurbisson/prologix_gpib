"""
Prologix GPIB-USB Controller Python Library

A comprehensive Python library for controlling Prologix GPIB-USB controllers
through serial communication. This library provides a high-level interface
for IEEE 488.1/488.2 compliant instruments.

Usage:
    from prologix_gpib import PrologixGpib
    
    # Create controller instance
    gpib = PrologixGpib("COM3", baudrate=9600)
    
    # Get an instrument at a specific address
    dmm = gpib.instrument(5)  # DMM at GPIB address 5
    
    # Send commands and read responses
    dmm.write("*IDN?")
    print(dmm.read())
    
    # Or use the convenience method for combined operations
    response = dvm.query("*IDN?")
    
    gpib.close()
"""

from .controller import PrologixGpib, PrologixError
from .instrument import GpibInstrument

__version__ = "1.0.0"
__all__ = ["PrologixGpib", "PrologixError", "GpibInstrument"]
