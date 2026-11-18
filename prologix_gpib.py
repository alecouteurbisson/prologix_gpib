"""
Prologix GPIB Controller Module

This module provides the main PrologixGpib class for controlling
the Prologix GPIB-USB controller through serial communication.
"""

import serial
from typing import Optional, Union, List
import time
import logging
# import instrument

# Configure logging
logger = logging.getLogger(__name__)

class GpibInstrument:
    """
    High-level interface for a single GPIB instrument.
    
    This class wraps communication with a specific GPIB instrument,
    handling address management and providing convenient methods
    for common operations.
    
    Args:
        controller: PrologixGpib controller instance
        address: Primary GPIB address (0-30)
        sad: Secondary address (96-126), optional
    """
    
    def __init__(self, controller, address: int, sad: Optional[int] = None):
        """
        Initialize the instrument interface.
        
        Args:
            controller: PrologixGpib controller instance
            address: Primary GPIB address (0-30)
            sad: Secondary address (96-126), optional
        """
        self._controller = controller
        self.address = address
        self.sad = sad
        
        # Set the instrument's address on the controller
        self._controller.set_address(address, sad)
    
    def write(self, command: str) -> None:
        """
        Send a command to the instrument.
        
        Args:
            command: Command string without trailing newline
        """
        self._controller.write(command)
    
    def read(
        self,
        terminator: Union[str, int] = "eoi",
        timeout: Optional[float] = None
    ) -> str:
        """
        Read response from the instrument.
        
        Args:
            terminator: 'eoi' for EOI detection, or ASCII value (0-255)
            timeout: Override default timeout (optional)
            
        Returns:
            Response string
        """
        return self._controller.read(terminator=terminator, timeout=timeout)
    
    def query(
        self,
        command: str,
        terminator: Union[str, int] = "eoi",
        timeout: Optional[float] = None
    ) -> str:
        """
        Send a command and read response (convenience method).
        
        Args:
            command: Command string without trailing newline
            terminator: 'eoi' for EOI detection, or ASCII value (0-255)
            timeout: Override default timeout (optional)
            
        Returns:
            Response string
        """
        self._controller.write(command)
        return self._controller.read(terminator=terminator, timeout=timeout)

    def run(self, script, subs = {}) -> None:
        """ 
        Run a script of device commands.
        
        Commands starting with ! are run as python commands (e.g. time.sleep(1.0))
        Symbols in braces are interpolated from dictionary subs
        If no substitution is found then the braces and their content are retained
        """
        for line in script.split('\n'):
            line = line.split('#')[0].strip()
            if line != '':
                if subs:
                    line = line.format(**subs)
                if line.startswith('!'):
                    exec(line[1:])
                else:
                    self.write(line)
    
    def identify(self) -> str:
        """
        Query instrument identification.
        
        Sends *IDN? command and returns the response.
        
        Returns:
            Instrument identification string
        """
        return self.query("*IDN?")
    
    def reset(self) -> None:
        """Send reset command to the instrument."""
        self.write("*RST")
    
    def status_query(self) -> int:
        """
        Query standard event status register.
        
        Returns:
            Status register value
        """
        response = self.query("*ESR?")
        return int(response.strip())
    
    def idn_match(self, pattern: str) -> bool:
        """
        Check if instrument identification matches a pattern.
        
        Args:
            pattern: Pattern to match (supports * wildcards)
            
        Returns:
            True if IDN matches the pattern
        """
        import fnmatch
        
        idn = self.identify()
        return fnmatch.fnmatch(idn, pattern)
    
    def wait_for_srq(self, timeout: float = 10.0) -> bool:
        """
        Wait for SRQ (Service Request) from instrument.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if SRQ was received, False on timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if self._controller.srq_status():
                return True
            time.sleep(0.1)
        
        return False
    
    def poll(self) -> int:
        """
        Perform serial poll on this instrument.
        
        Returns:
            Serial poll response byte
        """
        return self._controller.serial_poll(self.address, self.sad)
    
    def trigger(self) -> None:
        """Send Group Execute Trigger to this instrument."""
        self._controller.group_trigger([self.address])
    
    def clear(self) -> None:
        """Send Selected Device Clear (SDC) to this instrument."""
        self._controller.clear()
    
    def local(self) -> None:
        """Enable front panel operation of this instrument."""
        self._controller.local_mode()
    
    def remote(self) -> None:
        """Disable front panel operation of this instrument."""
        self._controller.remote_mode()
    
    # Context manager support
    def __enter__(self) -> 'GpibInstrument':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        pass
    
    # String representation
    def __repr__(self) -> str:
        if self.sad is not None:
            return f"GpibInstrument(address={self.address}, sad={self.sad})"
        return f"GpibInstrument(address={self.address})"



class InstrumentList:
    """
    Container for multiple GPIB instruments.
    
    Provides convenient access to multiple instruments
    through attribute or dictionary-style access.
    
    Args:
        controller: PrologixGpib controller instance
    """
    
    def __init__(self, controller):
        self._controller = controller
        self._instruments: dict = {}
    
    def add(self, name: str, address: int, sad: Optional[int] = None) -> GpibInstrument:
        """
        Add an instrument to the list.
        
        Args:
            name: Name for this instrument (used in attribute access)
            address: Primary GPIB address (0-30)
            sad: Secondary address (96-126), optional
            
        Returns:
            Created GpibInstrument instance
        """
        inst = self._controller.instrument(address, sad)
        self._instruments[name] = inst
        setattr(self, name, inst)
        return inst
    
    def get(self, name: str) -> Optional[GpibInstrument]:
        """Get instrument by name."""
        return self._instruments.get(name)
    
    def __getitem__(self, key: str) -> GpibInstrument:
        return self._instruments[key]
    
    def __setitem__(self, key: str, value: GpibInstrument) -> None:
        self._instruments[key] = value
        setattr(self, key, value)
    
    def __contains__(self, name: str) -> bool:
        return name in self._instruments
    
    def __iter__(self):
        return iter(self._instruments.values())
    
    def __len__(self) -> int:
        return len(self._instruments)

    
class PrologixError(Exception):
    """Base exception for Prologix-related errors."""
    pass


class PrologixGpib:
    """
    Main class for controlling a Prologix GPIB-USB controller.
    
    This class provides methods to communicate with the Prologix controller
    and manage GPIB instruments connected to it.
    
    Args:
        port: Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
        baudrate: Baud rate for serial communication (default: 9600)
        timeout: Read timeout in seconds (default: 1.0)
        address: Default GPIB address (default: 0)
        auto_mode: Enable read-after-write mode (default: True)
        eoi: Assert EOI with last byte (default: True)
        eos: End-of-line character (0=CR+LF, 1=CR, 2=LF, 3=None) (default: 1)
        debug: Enable debug logging (default: False)
        
    Example:
        >>> gpib = PrologixGpib('COM3', baudrate=9600)
        >>> gpib.connect()
        >>> dmm = gpib.instrument(5)
        >>> print(dmm.query('*IDN?'))
    """
    
    # Valid GPIB address range
    MIN_GPIB_ADDRESS = 0
    MAX_GPIB_ADDRESS = 30
    
    # Valid secondary address range
    MIN_SAD = 96
    MAX_SAD = 126
    
    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        address: int = 0,
        auto_mode: bool = True,
        eoi: bool = True,
        eos: int = 1,
        debug: bool = False
    ):
        """
        Initialize the Prologix GPIB controller.
        
        Args:
            port: Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
            baudrate: Baud rate for serial communication (default: 9600)
            timeout: Read timeout in seconds (default: 1.0)
            address: Default GPIB address (default: 0)
            auto_mode: Enable read-after-write mode (default: True)
            eoi: Assert EOI with last byte (default: True)
            eos: End-of-line character (0=CR+LF, 1=CR, 2=LF, 3=None) (default: 1)
            debug: Enable debug logging (default: False)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._address = address
        self._auto_mode = auto_mode
        self._eoi = eoi
        self._eos = eos
        
        # Serial connection
        self._ser: Optional[serial.Serial] = None
        
        # Instrument cache
        self._instruments: dict = {}
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
    
    def connect(self) -> None:
        """Establish serial connection to the Prologix controller."""
        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            # Give the device time to initialize
            time.sleep(0.5)
            
            # Configure initial settings
            self._write_command(f"++addr {self._address}")
            self._write_command(f"++auto {'1' if self._auto_mode else '0'}")
            self._write_command(f"++eoi {'1' if self._eoi else '0'}")
            self._write_command(f"++eos {self._eos}")
            
            logger.info(f"Connected to Prologix controller on {self.port}")
        except serial.SerialException as e:
            raise PrologixError(f"Failed to connect to {self.port}: {e}")
    
    def close(self) -> None:
        """Close the serial connection."""
        if self._ser and self._ser.is_open:
            self._ser.close()
            logger.info("Closed serial connection")
    
    def _write_command(self, command: str) -> None:
        """
        Write a command to the Prologix controller.
        
        Args:
            command: Command string without trailing newline
        """
        if not self._ser or not self._ser.is_open:
            raise PrologixError("Serial connection is not open")
        
        # Add line feed terminator
        cmd = f"{command}\n"
        self._ser.write(cmd.encode('ascii'))
        logger.debug(f"Sent: {cmd.strip()}")
    
    def _read_response(self, timeout: Optional[float] = None) -> str:
        """
        Read response from the Prologix controller.
        
        Args:
            timeout: Override default timeout (optional)
            
        Returns:
            Response string without trailing newline
        """
        if not self._ser or not self._ser.is_open:
            raise PrologixError("Serial connection is not open")
        
        # Temporarily set timeout if provided
        original_timeout = self._ser.timeout
        if timeout is not None:
            self._ser.timeout = timeout
        
        try:
            response = self._ser.readline()
            result = response.decode('ascii').strip()
            logger.debug(f"Received: {result}")
            return result
        finally:
            # Restore original timeout
            if timeout is not None:
                self._ser.timeout = original_timeout
    
    def _query(self, command: str, timeout: Optional[float] = None) -> str:
        """
        Send a command and read the response.
        
        Args:
            command: Command string without trailing newline
            timeout: Override default timeout (optional)
            
        Returns:
            Response string without trailing newline
        """
        self._write_command(command)
        return self._read_response(timeout=timeout)
    
    def get_version(self) -> str:
        """Get the Prologix controller firmware version."""
        return self._query("++ver")
    
    def set_address(self, address: int, sad: Optional[int] = None) -> None:
        """
        Set the primary GPIB address.
        
        Args:
            address: Primary GPIB address (0-30)
            sad: Secondary address (96-126), optional
        """
        if not self.MIN_GPIB_ADDRESS <= address <= self.MAX_GPIB_ADDRESS:
            raise ValueError(f"Address must be between {self.MIN_GPIB_ADDRESS} and {self.MAX_GPIB_ADDRESS}")
        
        if sad is not None:
            if not self.MIN_SAD <= sad <= self.MAX_SAD:
                raise ValueError(f"SAD must be between {self.MIN_SAD} and {self.MAX_SAD}")
            self._write_command(f"++addr {address} {sad}")
        else:
            self._write_command(f"++addr {address}")
        
        self._address = address
    
    def get_address(self) -> str:
        """Get the current GPIB address configuration."""
        return self._query("++addr")
    
    def set_auto_mode(self, enabled: bool) -> None:
        """
        Enable or disable read-after-write mode.
        
        Args:
            enabled: True to enable auto-read, False to disable
        """
        self._write_command(f"++auto {'1' if enabled else '0'}")
        self._auto_mode = enabled
    
    def get_auto_mode(self) -> bool:
        """Get current auto-read mode status."""
        response = self._query("++auto")
        return response == "1"
    
    def set_eoi(self, enabled: bool) -> None:
        """
        Enable or disable EOI assertion with last byte.
        
        Args:
            enabled: True to enable EOI, False to disable
        """
        self._write_command(f"++eoi {'1' if enabled else '0'}")
        self._eoi = enabled
    
    def get_eoi(self) -> bool:
        """Get current EOI status."""
        response = self._query("++eoi")
        return response == "1"
    
    def set_eos(self, eos: int) -> None:
        """
        Set end-of-line character.
        
        Args:
            eos: 0=CR+LF, 1=CR, 2=LF, 3=None
        """
        if not 0 <= eos <= 3:
            raise ValueError("EOS must be between 0 and 3")
        self._write_command(f"++eos {eos}")
        self._eos = eos
    
    def get_eos(self) -> int:
        """Get current EOS setting."""
        response = self._query("++eos")
        return int(response)
    
    def set_timeout(self, milliseconds: int) -> None:
        """
        Set read timeout in milliseconds.
        
        Args:
            milliseconds: Timeout value (1-3000 ms)
        """
        if not 1 <= milliseconds <= 3000:
            raise ValueError("Timeout must be between 1 and 3000 ms")
        self._write_command(f"++read_tmo_ms {milliseconds}")
    
    def get_timeout(self) -> int:
        """Get current read timeout in milliseconds."""
        response = self._query("++read_tmo_ms")
        return int(response)
    
    def serial_poll(self, address: Optional[int] = None, sad: Optional[int] = None) -> str:
        """
        Perform a serial poll of the specified instrument.
        
        Args:
            address: GPIB address (optional, uses current if not specified)
            sad: Secondary address (optional)
            
        Returns:
            Serial poll response byte
        """
        if address is not None:
            self.set_address(address, sad)
        
        return self._query("++spoll")
    
    def srq_status(self) -> bool:
        """
        Check SRQ (Service Request) status.
        
        Returns:
            True if SRQ is asserted, False otherwise
        """
        response = self._query("++srq")
        return response == "1"
    
    def group_trigger(self, addresses: List[int]) -> None:
        """
        Send Group Execute Trigger to multiple instruments.
        
        Args:
            addresses: List of GPIB addresses to trigger
        """
        addr_str = ' '.join(str(a) for a in addresses)
        self._write_command(f"++trg {addr_str}")
    
    def clear(self) -> None:
        """Send Selected Device Clear (SDC) to current instrument."""
        self._write_command("++clr")
    
    def ifc_assert(self) -> None:
        """Assert IFC signal to become Controller-In-Charge."""
        self._write_command("++ifc")
    
    def local_mode(self) -> None:
        """Enable front panel operation of current instrument."""
        self._write_command("++loc")
    
    def remote_mode(self) -> None:
        """Disable front panel operation of current instrument."""
        self._write_command("++llo")
    
    def listen_only(self, enabled: bool) -> None:
        """
        Enable or disable listen-only mode.
        
        Args:
            enabled: True to enable listen-only mode
        """
        self._write_command(f"++lon {'1' if enabled else '0'}")
    
    def get_status(self) -> int:
        """
        Get device status byte for DEVICE mode.
        
        Returns:
            Status byte (0-255)
        """
        response = self._query("++status")
        return int(response)
    
    def set_status(self, status: int) -> None:
        """
        Set device status byte for DEVICE mode.
        
        Args:
            status: Status byte (0-255)
        """
        if not 0 <= status <= 255:
            raise ValueError("Status must be between 0 and 255")
        self._write_command(f"++status {status}")
    
    def save_config(self, enabled: bool) -> None:
        """
        Enable or disable automatic config saving to EEPROM.
        
        Args:
            enabled: True to enable auto-save
        """
        self._write_command(f"++savecfg {'1' if enabled else '0'}")
    
    def reset(self) -> None:
        """Perform power-on reset of the controller."""
        self._write_command("++rst")
        # Wait for reset to complete
        time.sleep(5)
    
    def instrument(self, address: int, sad: Optional[int] = None) -> 'GpibInstrument':
        """
        Get an Instrument object for communication.
        
        Args:
            address: GPIB primary address (0-30)
            sad: Secondary address (96-126), optional
            
        Returns:
            GpibInstrument instance
        """
        if not self.MIN_GPIB_ADDRESS <= address <= self.MAX_GPIB_ADDRESS:
            raise ValueError(f"Address must be between {self.MIN_GPIB_ADDRESS} and {self.MAX_GPIB_ADDRESS}")
        
        key = (address, sad)
        if key not in self._instruments:
            self._instruments[key] = GpibInstrument(self, address, sad)
        
        return self._instruments[key]
    
    def query(self, command: str, timeout: Optional[float] = None) -> str:
        """
        Send a command and read response (convenience method).
        
        Args:
            command: Command string without trailing newline
            timeout: Override default timeout (optional)
            
        Returns:
            Response string
        """
        return self._query(command, timeout=timeout)
    
    def write(self, command: str) -> None:
        """
        Send a command without reading response.
        
        Args:
            command: Command string without trailing newline
        """
        self._write_command(command)
    
    def read(self, terminator: Union[str, int] = "eoi", timeout: Optional[float] = None) -> str:
        """
        Read data from the instrument.
        
        Args:
            terminator: 'eoi' for EOI detection, or ASCII value (0-255)
            timeout: Override default timeout (optional)
            
        Returns:
            Response string
        """
        if terminator == "eoi":
            response = self._query("++read eoi", timeout=timeout)
        elif isinstance(terminator, int):
            response = self._query(f"++read {terminator}", timeout=timeout)
        else:
            raise ValueError("Terminator must be 'eoi' or an integer ASCII value")
        
        return response
    
    def __enter__(self) -> 'PrologixGpib':
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


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

