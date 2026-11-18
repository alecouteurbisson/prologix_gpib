"""
Test suite for GpibInstrument class.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prologix_gpib.controller import PrologixGpib
from prologix_gpib.instrument import GpibInstrument


class TestGpibInstrument(unittest.TestCase):
    """Test cases for GpibInstrument class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock serial port
        self.mock_serial = MagicMock()
        
        with patch('serial.Serial', return_value=self.mock_serial):
            self.gpib = PrologixGpib('COM3')
            self.gpib._ser = self.mock_serial
        
        # Create instrument
        self.inst = GpibInstrument(self.gpib, 5)
    
    def test_initialization(self):
        """Test instrument initialization."""
        self.assertEqual(self.inst.address, 5)
        self.assertIsNone(self.inst.sad)
        self.assertEqual(self.inst._controller, self.gpib)
    
    def test_write_command(self):
        """Test command writing."""
        self.mock_serial.is_open = True
        
        self.inst.write("*IDN?")
        
        # Verify controller was called
        self.mock_serial.write.assert_called()
    
    def test_read_response(self):
        """Test response reading."""
        self.mock_serial.is_open = True
        self.mock_serial.readline.return_value = b"HP,34401A\n"
        
        response = self.inst.read()
        self.assertEqual(response, "HP,34401A")
    
    def test_query(self):
        """Test query (write + read)."""
        self.mock_serial.is_open = True
        self.mock_serial.readline.return_value = b"HP,34401A\n"
        
        response = self.inst.query("*IDN?")
        self.assertEqual(response, "HP,34401A")
    
    def test_identify(self):
        """Test instrument identification."""
        self.mock_serial.is_open = True
        self.mock_serial.readline.return_value = b"HEWLETT-PACKARD,34401A,12345678,1.2\n"
        
        idn = self.inst.identify()
        expected = "HEWLETT-PACKARD,34401A,12345678,1.2"
        self.assertEqual(idn, expected)
    
    def test_reset(self):
        """Test instrument reset."""
        self.mock_serial.is_open = True
        
        self.inst.reset()
        
        # Verify *RST was sent
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b"*RST", call_args)
    
    def test_status_query(self):
        """Test status register query."""
        self.mock_serial.is_open = True
        self.mock_serial.readline.return_value = b"32\n"
        
        status = self.inst.status_query()
        self.assertEqual(status, 32)
    
    def test_idn_match(self):
        """Test IDN pattern matching."""
        self.mock_serial.is_open = True
        self.mock_serial.readline.return_value = b"HEWLETT-PACKARD,34401A\n"
        
        # Test exact match
        self.assertTrue(self.inst.idn_match("HEWLETT-PACKARD,34401A,*"))
        
        # Test non-match
        self.assertFalse(self.inst.idn_match("AGILENT,*"))
    
    def test_poll(self):
        """Test serial poll."""
        self.mock_serial.is_open = True
        self.mock_serial.readline.return_value = b"0\n"
        
        result = self.inst.poll()
        self.assertEqual(result, "0")
    
    def test_trigger(self):
        """Test group trigger."""
        self.mock_serial.is_open = True
        
        self.inst.trigger()
        
        # Verify ++trg was sent with correct address
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b"++trg 5", call_args)
    
    def test_clear(self):
        """Test device clear."""
        self.mock_serial.is_open = True
        
        self.inst.clear()
        
        # Verify ++clr was sent
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b"++clr", call_args)
    
    def test_local_remote_mode(self):
        """Test local/remote mode control."""
        self.mock_serial.is_open = True
        
        # Remote mode (disable front panel)
        self.inst.remote()
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b"++llo", call_args)
        
        # Local mode (enable front panel)
        self.inst.local()
        call_args = self.mock_serial.write.call_args[0][0]
        self.assertIn(b"++loc", call_args)
    
    def test_repr(self):
        """Test string representation."""
        inst1 = GpibInstrument(self.gpib, 5)
        self.assertEqual(repr(inst1), "GpibInstrument(address=5)")
        
        inst2 = GpibInstrument(self.gpib, 9, 96)
        self.assertEqual(repr(inst2), "GpibInstrument(address=9, sad=96)")


class TestInstrumentList(unittest.TestCase):
    """Test cases for InstrumentList class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_serial = MagicMock()
        
        with patch('serial.Serial', return_value=self.mock_serial):
            self.gpib = PrologixGpib('COM3')
            self.gpib._ser = self.mock_serial
        
        from prologix_gpib.instrument import InstrumentList
        self.list = InstrumentList(self.gpib)
    
    def test_add_instrument(self):
        """Test adding instruments."""
        inst1 = self.list.add("dmm", 5)
        self.assertEqual(inst1.address, 5)
        
        inst2 = self.list.add("scope", 10)
        self.assertEqual(inst2.address, 10)
    
    def test_attribute_access(self):
        """Test attribute-style access."""
        self.list.add("dmm", 5)
        
        # Should be accessible as attribute
        self.assertIsNotNone(self.list.dmm)
        self.assertEqual(self.list.dmm.address, 5)
    
    def test_dict_style_access(self):
        """Test dictionary-style access."""
        self.list.add("dmm", 5)
        
        # Should be accessible as dict item
        self.assertEqual(self.list["dmm"].address, 5)
    
    def test_contains(self):
        """Test 'in' operator."""
        self.list.add("dmm", 5)
        
        self.assertIn("dmm", self.list)
        self.assertNotIn("scope", self.list)
    
    def test_iteration(self):
        """Test iteration over instruments."""
        self.list.add("dmm", 5)
        self.list.add("scope", 10)
        
        instruments = list(self.list)
        self.assertEqual(len(instruments), 2)
    
    def test_len(self):
        """Test length."""
        self.assertEqual(len(self.list), 0)
        
        self.list.add("dmm", 5)
        self.assertEqual(len(self.list), 1)


if __name__ == '__main__':
    unittest.main()
