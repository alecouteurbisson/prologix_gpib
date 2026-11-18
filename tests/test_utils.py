"""
Test suite for utility functions.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prologix_gpib.utils import (
    parse_scpi_response,
    parse_number,
    format_scpi_command,
    validate_address,
    escape_binary_data,
    unescape_binary_data,
    parse_idn,
    create_command_block
)


class TestParseSCPIResponse(unittest.TestCase):
    """Test parse_scpi_response function."""
    
    def test_simple_response(self):
        """Test simple key=value response."""
        result = parse_scpi_response("VOLTAGE=1.234")
        self.assertEqual(result["VOLTAGE"], "1.234")
    
    def test_multiple_responses(self):
        """Test multiple lines response."""
        result = parse_scpi_response("VOLTAGE=1.234\nCURRENT=0.5")
        self.assertEqual(result["VOLTAGE"], "1.234")
        self.assertEqual(result["CURRENT"], "0.5")


class TestParseNumber(unittest.TestCase):
    """Test parse_number function."""
    
    def test_integer(self):
        """Test integer parsing."""
        result = parse_number("42")
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)
    
    def test_float(self):
        """Test float parsing."""
        result = parse_number("3.14159")
        self.assertEqual(result, 3.14159)
        self.assertIsInstance(result, float)
    
    def test_scientific_notation(self):
        """Test scientific notation parsing."""
        result = parse_number("1.23E-4")
        self.assertEqual(result, 1.23e-4)
        self.assertIsInstance(result, float)
    
    def test_invalid_number(self):
        """Test invalid number handling."""
        with self.assertRaises(ValueError):
            parse_number("not_a_number")


class TestFormatSCPICommand(unittest.TestCase):
    """Test format_scpi_command function."""
    
    def test_no_parameters(self):
        """Test command without parameters."""
        result = format_scpi_command("*IDN")
        self.assertEqual(result, "*IDN")
    
    def test_single_parameter(self):
        """Test command with single parameter."""
        result = format_scpi_command("MEAS:VOLT", [1.5])
        self.assertEqual(result, "MEAS:VOLT 1.5")
    
    def test_multiple_parameters(self):
        """Test command with multiple parameters."""
        result = format_scpi_command("SENS:CURR", [0.1, 100, 1e-6])
        self.assertIn("SENS:CURR", result)
    
    def test_string_parameter(self):
        """Test command with string parameter."""
        result = format_scpi_command("CONF:VOLT", ["AUTO"])
        self.assertEqual(result, "CONF:VOLT AUTO")


class TestValidateAddress(unittest.TestCase):
    """Test validate_address function."""
    
    def test_valid_primary_address(self):
        """Test valid primary addresses."""
        for addr in [0, 15, 30]:
            validate_address(addr)
        
        # Should not raise
        self.assertTrue(True)
    
    def test_invalid_primary_address(self):
        """Test invalid primary address handling."""
        with self.assertRaises(ValueError):
            validate_address(31)
        
        with self.assertRaises(ValueError):
            validate_address(-1)
    
    def test_valid_secondary_address(self):
        """Test valid secondary addresses."""
        for addr in [96, 100, 126]:
            validate_address(addr, allow_sad=True)
    
    def test_invalid_secondary_address(self):
        """Test invalid secondary address handling."""
        with self.assertRaises(ValueError):
            validate_address(35, allow_sad=True)
        
        with self.assertRaises(ValueError):
            validate_address(95, allow_sad=True)


class TestBinaryDataEscaping(unittest.TestCase):
    """Test binary data escaping functions."""
    
    def test_escape_special_chars(self):
        """Test escaping of special characters."""
        # Special chars: CR=13, LF=10, ESC=27, +=43
        data = bytes([0, 13, 27, 43, 1])
        
        escaped = escape_binary_data(data)
        
        # Verify escaping
        expected = bytes([0, 27, 13, 27, 27, 27, 43, 1])
        self.assertEqual(escaped, expected)
    
    def test_unescape_special_chars(self):
        """Test unescaping of special characters."""
        # Escaped data: [ESC][CR] = escaped CR
        data = bytes([0, 27, 13, 1, 27, 27, 2])
        
        unescaped = unescape_binary_data(data)
        
        # Verify unescaping
        expected = bytes([0, 13, 1, 27, 2])
        self.assertEqual(unescaped, expected)
    
    def test_escape_unescape_roundtrip(self):
        """Test escape/unescape round-trip."""
        original = bytes(range(256))
        
        escaped = escape_binary_data(original)
        unescaped = unescape_binary_data(escaped)
        
        # Should match original
        self.assertEqual(unescaped, original)


class TestParseIDN(unittest.TestCase):
    """Test parse_idn function."""
    
    def test_full_idn(self):
        """Test full identification string."""
        idn = "HEWLETT-PACKARD,34401A,12345678,1.2"
        result = parse_idn(idn)
        
        self.assertEqual(result["manufacturer"], "HEWLETT-PACKARD")
        self.assertEqual(result["model"], "34401A")
        self.assertEqual(result["serial"], "12345678")
        self.assertEqual(result["firmware"], "1.2")
    
    def test_minimal_idn(self):
        """Test minimal identification string."""
        idn = "TEST"
        result = parse_idn(idn)
        
        self.assertEqual(result["manufacturer"], "TEST")
        self.assertEqual(result["model"], "")
        self.assertEqual(result["serial"], "")
        self.assertEqual(result["firmware"], "")


class TestCreateCommandBlock(unittest.TestCase):
    """Test create_command_block function."""
    
    def test_single_command(self):
        """Test single command."""
        result = create_command_block(["*IDN?"])
        self.assertEqual(result, "*IDN?")
    
    def test_multiple_commands(self):
        """Test multiple commands."""
        commands = ["*RST", "*CLS", "*IDN?"]
        result = create_command_block(commands)
        
        self.assertEqual(result, "*RST;*CLS;*IDN?")


if __name__ == '__main__':
    unittest.main()
