#!/usr/bin/env python
"""
Example usage of the Prologix GPIB library.

This script demonstrates various ways to use the PrologixGpib class
to control instruments connected via a Prologix GPIB-USB controller.
"""

import time
from prologix_gpib import PrologixGpib, GpibInstrument

def basic_example():
    """Basic example: send commands and read responses."""
    print("=== Basic Example ===")
    
    # Connect to the Prologix controller
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        # Get an instrument at address 2
        dmm = gpib.instrument(2)
        
        # Query identification
        print(f"ID: {dmm.identify()}")
        
        # Send a command and read response
        dmm.write("*RST")  # Reset the instrument
        time.sleep(0.1)
        
        # Query voltage measurement
        #voltage = dmm.query("MEAS:VOLT?")
        #print(f"Voltage: {voltage}")


def multiple_instruments_example():
    """Example with multiple instruments."""
    print("\n=== Multiple Instruments Example ===")
    
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        # Create instrument objects
        dmm = gpib.instrument(5, name="dmm")  # Digital Multimeter
        psu = gpib.instrument(1, name="psu")  # Power Supply
        
        # Query identification of both
        print(f"DMM: {dmm.identify()}")
        print(f"PSU: {psu.identify()}")


def instrument_list_example():
    """Example using InstrumentList for managing multiple instruments."""
    print("\n=== Instrument List Example ===")
    
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        # Create an instrument list
        from prologix_gpib.instrument import InstrumentList
        instruments = InstrumentList(gpib)
        
        # Add instruments with convenient names
        instruments.add("dmm", 5)
        instruments.add("scope", 10)
        instruments.add("psu", 1)
        
        # Access via attribute
        print(f"DMM: {instruments.dmm.identify()}")
        
        # Or access via dictionary style
        print(f"PSU: {instruments['psu'].identify()}")


def scpi_commands_example():
    """Example using SCPI command formatting."""
    print("\n=== SCPI Commands Example ===")
    
    from prologix_gpib.utils import format_scpi_command
    
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        dmm = gpib.instrument(5)
        
        # Format SCPI commands
        cmd1 = format_scpi_command("CONF:VOLT", ["DC"])
        cmd2 = format_scpi_command("SENS:VOLT:RANG", [10])
        
        print(f"Command 1: {cmd1}")
        print(f"Command 2: {cmd2}")


def event_driven_example():
    """Example using SRQ (Service Request) for event-driven communication."""
    print("\n=== Event-Driven Example ===")
    
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        dmm = gpib.instrument(5)
        
        # Configure instrument to generate SRQ on measurement ready
        dmm.write("*SRE 1")  # Enable service request
        dmm.write("*ESE 1")  # Enable standard event
        
        print("Waiting for measurement completion...")
        
        # Wait up to 10 seconds for SRQ
        if dmm.wait_for_srq(timeout=10.0):
            print("SRQ received! Reading measurement...")
            result = dmm.query("FETC?")
            print(f"Result: {result}")
        else:
            print("Timeout waiting for SRQ")


def binary_data_example():
    """Example handling binary data (e.g., oscilloscope trace)."""
    print("\n=== Binary Data Example ===")
    
    from prologix_gpib.utils import escape_binary_data, unescape_binary_data
    
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        scope = gpib.instrument(10)
        
        # For binary data transmission
        scope.write("CURVE?")  # Get waveform
        
        # Read until EOI (End of Integration)
        raw_data = scope.read(terminator="eoi")
        
        print(f"Received {len(raw_data)} bytes")


def advanced_configuration_example():
    """Example showing advanced configuration options."""
    print("\n=== Advanced Configuration Example ===")
    
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        # Configure the controller
        gpib.set_auto_mode(True)
        gpib.set_eoi(True)
        gpib.set_eos(1)  # CR terminator
        
        # Get current configuration
        print(f"Auto mode: {gpib.get_auto_mode()}")
        print(f"EOI enabled: {gpib.get_eoi()}")
        print(f"EOS setting: {gpib.get_eos()}")


def context_manager_example():
    """Example using context managers for automatic cleanup."""
    print("\n=== Context Manager Example ===")
    
    # Using PrologixGpib as context manager
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        dmm = gpib.instrument(5)
        
        with dmm:  # Instrument also supports context manager
            print(f"ID: {dmm.identify()}")
    
    # Connection is automatically closed here


def main():
    """Run all examples."""
    print("Prologix GPIB Library Examples")
    print("=" * 40)
    
    # Note: These examples assume a Prologix controller connected to COM10
    # Modify the port name as needed for your system
    
    try:
        basic_example()
        multiple_instruments_example()
        instrument_list_example()
        scpi_commands_example()
        event_driven_example()
        binary_data_example()
        advanced_configuration_example()
        context_manager_example()
        
        print("\n" + "=" * 40)
        print("All examples completed!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. Prologix controller is connected")
        print("2. Correct COM port is specified")
        print("3. Required dependencies are installed")


if __name__ == "__main__":
    main()
