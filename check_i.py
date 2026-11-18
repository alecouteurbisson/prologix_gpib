#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
import time
from prologix_gpib import PrologixGpib, GpibInstrument
from serial_inst import SerialInst
import matplotlib.pyplot as plt

with PrologixGpib('COM10', baudrate=9600) as gpib:
    smu = gpib.instrument(2)
    smu.write("C,*RST")                 # DCL and parameter initialization
    time.sleep(0.1) 
    smu.write("*CLS")                   # Status byte initialization

    dmm = SerialInst('COM14', 9600)
    dmm.write("SYST:REM")
    dmm.write("*RST")

    smu.write("MD0")                    # DC mode
    smu.write("RS1")                    # 4-wire
    smu.write("IF")                     # Current forcing
    smu.write("SIR1")                   # 3mA Range
    smu.write("SOI0")                   # 0 output
    smu.write("OPR")                    # Operate

    x = []
    y = []
    for ix in range(-50,51):
        i = 0.00001 * ix
        ii = "{:.6f}".format(i)
        smu.write("SOI" + ii)
        time.sleep(2.0)
        out=dmm.query('MEAS:CURR:DC? DEF,DEF', 1.0)
        print(ii, out)
        x.append(i)
        y.append(i - float(out))

    smu.write("SBY")
    dmm.write("SYST:LOC")

    plt.style.use('ggplot')

    plt.plot(x, y, marker = ".")


    plt.tight_layout()
    plt.show()