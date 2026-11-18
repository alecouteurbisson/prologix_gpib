"""
Prologix GPIB Controller Module

This module provides the main PrologixGpib class for controlling
the Prologix GPIB-USB controller through serial communication.
"""

import serial
from typing import Optional, Union, List
import time
import logging
import instrument

# Configure logging
logger = logging.getLogger(__name__)


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
            self._instruments[key] = instrument.GpibInstrument(self, address, sad)
        
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
