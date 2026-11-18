#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
import time
from prologix_gpib import PrologixGpib, GpibInstrument


def sweep():
    """Sweep an LED."""
    print("=== Sweep Example ===")
    
    # Connect to the Prologix controller
    with PrologixGpib('COM10', baudrate=9600) as gpib:
        # Get an instrument at address 2
        smu = gpib.instrument(2)
            
        smu.write("C,*RST")                 # DCL and parameter initialization
        time.sleep(0.1) 
        smu.write("*CLS")                   # Status byte initialization
        smu.write("*SRE8")                  # Sets bit 3 of the service request enable register to 1.
        smu.write("DSE8192")                # Sets bit 13 of the device event enable register to 1.
        smu.write("S0")                     # SRQ transmission mode
        smu.write("IF,F1")                  # Current source / measure voltage
        smu.write("MD2")                    # Sweep source mode
        smu.write("RS1")                    # 4 wire mode
        smu.write("SN-0.001,0.001,0.00001")  # Linear sweep .1mA to 20mA 
        smu.write("SP3,4,100")              # Hold time: 3ms, Meas delay time: 4ms Period: 100ms
        smu.write("ST1,RL")                 # Memory store ON, Memory clear
        smu.write("OPR")                    # Operate
        smu.write("*TRG")                   # Start sweep
        if(smu.wait_for_srq(30.0)):         # Wait for sweep end
            smu.write("SBY")                # Output to standby
            smu.write("OH0")                # Output header off (removes initial data type code)
            smu.write("DL2")                # Set delimiter to EOI
            smu.write("RN1,0")              # Read data buffer
            y = []
            start = False
            while(True):
                data = smu.read()
                if(data == "+8.88888E+30"): # Sentinel value for unused data cell
                    break

                print(data)
                if(start):
                    y.append(float(data))

                if(data == ''):             # skip data util there is a blank line (why is this needed?)
                    start = True
                  
            smu.write("RN0,0")              # Release data buffer

            return y
        else:
            print("Timeout")
            exit(1)

y = sweep()

# This prints
# 1
# 1
# last reading
#
# sweep readings...

plt.style.use('ggplot')

x = np.arange(-0.0010, 0.00101, 0.00001)
plt.plot(x, y)


plt.tight_layout()
plt.show()

