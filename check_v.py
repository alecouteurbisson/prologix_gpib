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

    smu.write("MD0")
    smu.write("VF")
    smu.write("SOV0")
    smu.write("OPR")

    x = []
    y = []
    for v in range(-15, 16):
        smu.write("SOV" + str(v))
        time.sleep(1.0)
        out=dmm.query('MEAS:VOLT:DC? DEF,DEF', 1.0)
        print(v, out)
        x.append(v)
        y.append(v - float(out))

    smu.write("SBY")
    dmm.write("SYST:LOC")

    plt.style.use('ggplot')

    plt.plot(x, y)


    plt.tight_layout()
    plt.show()