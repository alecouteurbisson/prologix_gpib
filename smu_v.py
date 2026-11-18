import pyvisa

rm = pyvisa.ResourceManager('@py')
gpib = rm.open_resource("ASRL14::INSTR", read_termination = '\n', write_termination = '\n', baud_rate = 9600)

gpib.write('++mode 1')                  # controller mode
gpib.write('++auto 1')                  # automatically get the response if any
gpib.write('++addr 2')                  # device address 2
gpib.write('++read_tmo_ms 1000')        # read timeout
gpib.write('++eoi 1')                   # enable EOI with last trasmitted character
gpib.write('++eos 3')                   # append nothing to commands
gpib.write('++eot_enable 1')            # Append character to response when EOI detected
gpib.write('++eot_char 10')             # Character appended (LF)

print(gpib.query('*IDN?'))