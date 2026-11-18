# Prologix GPIB Python Library

A comprehensive Python library for controlling Prologix GPIB-USB controllers through serial communication. This library provides a high-level interface for IEEE 488.1/488.2 compliant instruments.

## Features

- **Easy-to-use API**: Simple, intuitive interface for GPIB communication
- **Multiple instrument support**: Manage multiple instruments with ease
- **SCPI command formatting**: Helper functions for SCPI command construction
- **Binary data handling**: Proper escaping and unescaping of binary data
- **Event-driven operations**: SRQ (Service Request) monitoring
- **Context manager support**: Automatic resource cleanup
- **Comprehensive error handling**: Custom exceptions for all error conditions

## Requirements

- Python 3.7+
- pyserial library (`pip install pyserial`)

## Examples

There are a bunch of examples written for an ADCMMT 6240A SMU


## Quick Start

```python
from prologix_gpib import PrologixGpib

# Connect to the controller
with PrologixGpib('COM3', baudrate=9600) as gpib:
    # Get an instrument at address 5
    dmm = gpib.instrument(5)
    
    # Query identification
    print(dmm.identify())
    
    # Send a command and read response
    voltage = dmm.query("MEAS:VOLT?")
    print(f"Voltage: {voltage}")
```

## Usage Examples

### Basic Communication

```python
from prologix_gpib import PrologixGpib

gpib = PrologixGpib('COM3', baudrate=9600)
gpib.connect()

dmm = gpib.instrument(5)

# Send command without reading response
dmm.write("*RST")

# Read response
response = dmm.read()

# Combined write and read (query)
idn = dmm.query("*IDN?")
print(idn)

gpib.close()
```

### Multiple Instruments

```python
from prologix_gpib import PrologixGpib

with PrologixGpib('COM3', baudrate=9600) as gpib:
    # Create instruments at different addresses
    dmm = gpib.instrument(5)
    scope = gpib.instrument(10)
    
    # Query both
    print(f"DMM: {dmm.identify()}")
    print(f"Scope: {scope.identify()}")
```

### Instrument List

```python
from prologix_gpib import PrologixGpib
from prologix_gpib.instrument import InstrumentList

with PrologixGpib('COM3', baudrate=9600) as gpib:
    instruments = InstrumentList(gpib)
    
    # Add instruments with convenient names
    instruments.add("dmm", 5)
    instruments.add("scope", 10)
    
    # Access via attribute or dictionary style
    print(instruments.dmm.identify())
    print(instruments["dmm"].identify())
```

### Event-Driven Communication

```python
from prologix_gpib import PrologixGpib

with PrologixGpib('COM3', baudrate=9600) as gpib:
    dmm = gpib.instrument(5)
    
    # Configure for SRQ
    dmm.write("*SRE 1")
    dmm.write("*ESE 1")
    
    # Wait for measurement completion
    if dmm.wait_for_srq(timeout=10.0):
        result = dmm.query("FETC?")
        print(f"Result: {result}")
```

### Binary Data Handling

```python
from prologix_gpib import PrologixGpib
from prologix_gpib.utils import escape_binary_data, unescape_binary_data

with PrologixGpib('COM3', baudrate=9600) as gpib:
    scope = gpib.instrument(10)
    
    # Get waveform data
    scope.write("CURVE?")
    
    # Read until EOI (End of Integration)
    raw_data = scope.read(terminator="eoi")
```

## API Reference

### PrologixGpib Class

Main class for controlling the Prologix GPIB-USB controller.

```python
PrologixGpib(
    port: str,
    baudrate: int = 9600,
    timeout: float = 1.0,
    address: int = 0,
    auto_mode: bool = True,
    eoi: bool = True,
    eos: int = 1,
    debug: bool = False
)
```

#### Methods

- `connect()`: Establish serial connection
- `close()`: Close serial connection
- `instrument(address, sad=None)`: Get instrument object
- `query(command, timeout=None)`: Send command and read response
- `write(command)`: Send command without reading
- `read(terminator="eoi", timeout=None)`: Read response
- `run(script, subs={})`: Run a script with variable interpolation

#### Configuration Methods

- `set_address(address, sad=None)`: Set GPIB address
- `get_address()`: Get current address
- `set_auto_mode(enabled)`: Enable/disable auto-read
- `get_auto_mode()`: Get auto-read status
- `set_eoi(enabled)`: Enable/disable EOI
- `get_eoi()`: Get EOI status
- `set_eos(value)`: Set EOS character (0-3)
- `get_eos()`: Get EOS setting
- `set_timeout(milliseconds)`: Set read timeout

#### Utility Methods

- `serial_poll(address, sad=None)`: Perform serial poll
- `srq_status()`: Check SRQ status
- `group_trigger(addresses)`: Send group trigger
- `clear()`: Send device clear
- `ifc_assert()`: Assert IFC signal
- `local_mode()`: Enable local mode
- `remote_mode()`: Disable local mode

### GpibInstrument Class

High-level interface for a single GPIB instrument.

```python
GpibInstrument(controller, address: int, sad=None)
```

#### Methods

- `write(command)`: Send command to instrument
- `read(terminator="eoi", timeout=None)`: Read response
- `query(command, terminator="eoi", timeout=None)`: Send and read
- `identify()`: Query instrument ID
- `reset()`: Reset instrument (*RST)
- `status_query()`: Get status register
- `wait_for_srq(timeout=10.0)`: Wait for SRQ
- `poll()`: Perform serial poll
- `trigger()`: Send group trigger
- `clear()`: Send device clear
- `local()`: Enable local mode
- `remote()`: Disable local mode

### Utility Functions

- `parse_scpi_response(response)`: Parse SCPI response
- `parse_number(value)`: Parse string to number
- `format_scpi_command(command, parameters=None)`: Format SCPI command
- `validate_address(address, allow_sad=False)`: Validate GPIB address
- `escape_binary_data(data)`: Escape binary data for transmission
- `unescape_binary_data(data)`: Unescape received binary data
- `parse_idn(idn_string)`: Parse instrument ID string

## Prologix Controller Commands Supported

All major Prologix commands are supported:

| Command | Description |
|---------|-------------|
| ++addr  | Set GPIB address |
| ++auto  | Enable/disable auto-read |
| ++eoi   | Control EOI assertion |
| ++eos   | Set EOS character |
| ++read_tmo_ms | Set read timeout |
| ++ver   | Get firmware version |
| ++spoll | Serial poll |
| ++srq   | Check SRQ status |
| ++trg   | Group trigger |
| ++clr   | Device clear |
| ++ifc   | Assert IFC |
| ++loc   | Local mode |
| ++llo   | Remote mode |

## Error Handling

The library defines a custom exception:

```python
from prologix_gpib import PrologixError

try:
    gpib = PrologixGpib('COM3')
    gpib.connect()
except PrologixError as e:
    print(f"Connection failed: {e}")
```

