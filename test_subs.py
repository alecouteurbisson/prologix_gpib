
def run(script, subs = {}) -> None:
    """ 
    Run a script of device commands.
    
    Commands starting with ! are run as python commands (e.g. time.sleep(1.0))
    Symbols in braces are interpolated from subs
    """
    for line in script.split('\n'):
        line = line.split('#')[0].strip()
        if line != '':
            if subs:
                line = line.format(**subs)
            if line.startswith('!'):
                print('exec ', line[1:])
            else:
                print(line)

setup = """
C,*RST                   # DCL and parameter initialization
!time.sleep(0.1)   
*CLS                     # Status byte initialization
*SRE8                    # Sets bit 3 of the service request enable register to 1.
DSE8192                  # Sets bit 13 of the device event enable register to 1.
S0                       # SRQ transmission mode
IF,{measure}             # Current source / measure voltage
MD2                      # Sweep source mode
RS1                      # 4 wire mode
SN-0.001,0.001,0.00001   # Linear sweep .1mA to 20mA 
SP3,4,10                 # Hold time: 3ms, Meas delay time: 4ms Period: 100ms
ST1,RL                   # Memory store ON, Memory clear
OPR                      # Operate
*TRG                     # Start 
"""

run(setup, {'measure': 'F2'})
print()
run(setup, {'measure': 'F3'})
print()
run(setup)

