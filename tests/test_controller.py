"""
Test suite for PrologixGpib controller class.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prologix_gpib.controller import PrologixGpib, PrologixError


class TestPrologixGpib(unittest.TestCase):
    """Test cases for PrologixGpib controller."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock serial port
        self.mock_serial = MagicMock()
        
        with patch('serial.Serial', return_value=self.mock_serial):
            self.gpib = PrologixGpib('COM3', baudrate=9600, timeout=1.0)
    
    def test_initialization(self):
        """Test controller initialization."""
        self.assertEqual(self.gpib.port, 'COM3')
        self.assertEqual(self.gpib.baudrate, 9600)
        self.assertEqual(self.gpib.timeout, 1.0)
        self.assertEqual(self.gpib._address, 0)
    
    def test_connect(self):
        """Test serial connection."""
        self.mock_serial.is_open = True
        
        with patch('serial.Serial', return_value=self.mock_serial):
            gpib = PrologixGpib('COM3')
            gpib.connect()
            
            # Verify serial was called
            self.assertTrue(gpib._ser is not None)
    
    def test_connect_failure(self):
        """Test connection failure handling."""
        with patch('serial.Serial', side_effect=Exception("Port not found")):
            with self.assertRaises(PrologixError):
                gpib = PrologixGpib('INVALID_PORT')
                gpib.connect()
    
    def test_set_address(self):
        """Test setting GPIB address."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        # Test valid address
        self.gpib.set_address(5)
        
        # Verify command was sent
        self.mock_serial.write.assert_called()
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b'++addr 5', call_args)
    
    def test_set_invalid_address(self):
        """Test invalid address handling."""
        with self.assertRaises(ValueError):
            self.gpib.set_address(31)
        
        with self.assertRaises(ValueError):
            self.gpib.set_address(-1)
    
    def test_get_version(self):
        """Test firmware version query."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        # Mock response
        self.mock_serial.readline.return_value = b'6.0\n'
        
        version = self.gpib.get_version()
        self.assertEqual(version, '6.0')
    
    def test_auto_mode(self):
        """Test auto-read mode control."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        # Enable auto mode
        self.gpib.set_auto_mode(True)
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b'++auto 1', call_args)
        
        # Disable auto mode
        self.gpib.set_auto_mode(False)
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b'++auto 0', call_args)
    
    def test_eoi_control(self):
        """Test EOI control."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        # Enable EOI
        self.gpib.set_eoi(True)
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b'++eoi 1', call_args)
    
    def test_eos_control(self):
        """Test EOS control."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        # Test valid EOS values
        for eos in range(4):
            self.gpib.set_eos(eos)
            call_args = self.mock_serial.write.call_args[0][0]
            self.assertIn(f'++eos {eos}'.encode(), call_args)
    
    def test_invalid_eos(self):
        """Test invalid EOS value handling."""
        with self.assertRaises(ValueError):
            self.gpib.set_eos(4)
        
        with self.assertRaises(ValueError):
            self.gpib.set_eos(-1)
    
    def test_timeout_setting(self):
        """Test timeout configuration."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        # Test valid timeout
        self.gpib.set_timeout(500)
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b'++read_tmo_ms 500', call_args)
    
    def test_invalid_timeout(self):
        """Test invalid timeout handling."""
        with self.assertRaises(ValueError):
            self.gpib.set_timeout(0)  # Below minimum
        
        with self.assertRaises(ValueError):
            self.gpib.set_timeout(3001)  # Above maximum
    
    def test_serial_poll(self):
        """Test serial poll functionality."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        # Mock response
        self.mock_serial.readline.return_value = b'0\n'
        
        result = self.gpib.serial_poll(5)
        self.assertEqual(result, '0')
    
    def test_srq_status(self):
        """Test SRQ status query."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        # Mock responses for both states
        self.mock_serial.readline.return_value = b'1\n'
        self.assertTrue(self.gpib.srq_status())
        
        self.mock_serial.readline.return_value = b'0\n'
        self.assertFalse(self.gpib.srq_status())
    
    def test_group_trigger(self):
        """Test group trigger command."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        addresses = [1, 5, 10]
        self.gpib.group_trigger(addresses)
        
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b'++trg 1 5 10', call_args)
    
    def test_instrument_creation(self):
        """Test instrument object creation."""
        self.mock_serial.is_open = True
        self.gpib._ser = self.mock_serial
        
        inst = self.gpib.instrument(5)
        
        # Check instrument was created
        self.assertIsNotNone(inst)
        self.assertEqual(inst.address, 5)
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with patch('serial.Serial', return_value=self.mock_serial) as mock_ser:
            with PrologixGpib('COM3') as gpib:
                # Inside context
                self.assertTrue(gpib._ser.is_open)
            
            # Outside context - should be closed
            mock_ser.return_value.close.assert_called()
    
    def test_binary_data_escaping(self):
        """Test binary data escaping functionality."""
        from prologix_gpib.utils import escape_binary_data
        
        # Test data with special characters
        data = bytes([0, 13, 27, 43, 1])
        
        escaped = escape_binary_data(data)
        
        # Verify ESC (27) is added before special chars
        expected = bytes([0, 27, 13, 27, 27, 27, 43, 1])
        self.assertEqual(escaped, expected)


class TestPrologixError(unittest.TestCase):
    """Test PrologixError exception class."""
    
    def test_error_creation(self):
        """Test error instantiation."""
        error = PrologixError("Test error message")
        self.assertEqual(str(error), "Test error message")


if __name__ == '__main__':
    unittest.main()
