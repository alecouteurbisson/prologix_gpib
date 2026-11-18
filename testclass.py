from prologix_gpib import PrologixGpib, GpibInstrument
import inspect

# Connect to the Prologix controller
with PrologixGpib('COM10', baudrate=9600) as gpib:
    # Get an instrument at address 2
    smu = gpib.instrument(2)
    print(inspect.getmembers(smu))