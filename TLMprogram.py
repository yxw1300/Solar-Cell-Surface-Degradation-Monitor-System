import pyvisa  # PyVISA module, for GPIB comms
import time  # to allow pause between measurements
import os  # Filesystem manipulation - mkdir, paths etc.
import numpy as np    # enable NumPy numerical analysis
import matplotlib.pyplot as plt  # for python-style plottting, like 'ax1.plot(x,y)'
import csv
#SaveFiles = True   # Save the plot & data?  Only display if False.


def keithley_sweep_function():
    '''
        Program requires the installation of NI-488.2 & NI-VISA & pyvisa/pyvisa-pi
        ''' 



    # Open Visa connections to instruments
    rm = pyvisa.ResourceManager()
    print ('Detected connected instrument:',rm.list_resources())
        #keithley = rm.open_resource(  'GPIB0::24::INSTR' )
    keithley =rm.open_resource("GPIB::"+Keithley_GPIB_Addr+"::INSTR")
        # Setup electrodes as voltage source
    keithley.write("*RST")
    print("reset the instrument")
    time.sleep(0.5)    # add second between
    keithley.write(":SOUR:FUNC:MODE CURR")
    #keithley.write(":SYST:RESN ON")#Eabling 4-wire
    #keithley.write(":SENS:FUNC 'CURR:DC' ")
    keithley.write(":SENS:FUNC:CONC OFF")
    keithley.write(":SENS:FUNC 'RES'")
    keithley.write(":SENS:RES:MODE MAN")
    #keithley.write(":SENS:VOLT:PROT 10")
    keithley.write(":SYST:RSEN ON")
    keithley.write(":SENS:VOLT:PROT:LEV " + str(VoltageCompliance))
    #keithley.write(":SENS:CURR:RANGE:AUTO 1")   # set current reading range to auto (boolean)
    keithley.write(":OUTP ON")                    # Output on    


    # Loop to sweep voltage
    Voltage=[]
    Current = []
    Resistance=[]
    for V in np.linspace(float(start), float(stop), num=int(numpoints), endpoint=True):
    #Voltage.append(V)
        print("Current set to: " + str(V) + " A" )
        keithley.write(":SOUR:CURR " + str(V))
        time.sleep(0.1)    # add second between
        data = keithley.query(":READ?")   #returns string with many values (V, I, ...)
        answer = data.split(',')    # remove delimiters, return values into list elements
        list = eval(data)    # convert to number
           # I=list[2]
            #Current.append( I )

           # vread = eval( answer.pop(0) )
           # Voltage.append(vread)

        R=list[2]
        Resistance.append(R)
            #Current.append(  I  )          # read the current

            #print("--> Current = " + str(Current[-1]) + ' A')   # print last read value
        print ("-->Resistance Reading:",Resistance[-1],"Ohm")
        #end for(V)
    keithley.write(":OUTP OFF")     # turn off


    keithley.write("SYSTEM:KEY 23") # go to local control
    keithley.close()


    return np.mean(Resistance)

import pyfirmata
from pyfirmata import ArduinoDue
from pyfirmata import INPUT,OUTPUT,PWM
import scipy.optimize as opt

def lin_fit(x,k,b):
    y=k*x+b
    return y

import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
for p in ports:
    print (p)
        
print ()
        
        #Here needs to define communication port. Try to find a way for auto detect or user input
board = ArduinoDue("COM3")
it = pyfirmata.util.Iterator(board)
it.start()
    
i_pin_list = []
v_pin_list = []
    
def main():
    

    for i in range(15,-1, -2):
        i_pin_name = "d:" + str(i + 23) + ":o" # Create current pin name, example: d:12:o is equal to pin 12 out
        v_pin_name = "d:" + str(i + 23 + 1) + ":o" # create voltage pin name, just 1 more than current pin
        i_pin = board.get_pin(i_pin_name)
        v_pin = board.get_pin(v_pin_name)
        i_pin.write(1)
        v_pin.write(1)
        i_pin_list.append(i_pin)
        v_pin_list.append(v_pin)
    resistance_list = []
        # Loop through each pair of pins (each pair is consecutive 1 and 2, 3 and 4, etc...
    for i in range(0,len(i_pin_list),1):
        i_pin = i_pin_list[i]
        v_pin = v_pin_list[i]
            # Turn on pins
        i_pin.write(0)
        v_pin.write(0)

        time.sleep(0.5) # Pause around keithley

            # Run keithley sweep and append resistance value to resistance list for later
        try:
            resistance = keithley_sweep_function()
            print ("Average R=",resistance,"Ohm")
            #resistivity = resistance / ((i + 1)*.001)  #refine this later 
            resistance_list.append(resistance)
        except Exception as e:
            print("Error running keithley sweep. Exiting Script")
            print(e)
            exit()

        print ("Sweeping done!")
        print ()
        time.sleep(0.5)

            # Turn off pins
        i_pin.write(1)
        v_pin.write(1)

    L=np.arange (0.002,0.018,0.002)   #grid line distance 
    plt.figure(figsize=(10,8))

    plt.xlabel('Distance (m)')
    plt.ylabel(r"Resistance $\Omega$")

    popt,pcov=opt.curve_fit(lin_fit,L,resistance_list)
    uncertainties = [np.sqrt(pcov[i][i]) for i in range(len(pcov))]
    slope=popt[0]
    intercept=popt[1]
    w=1e-2  #length of the grild line in m
    Rc=intercept/2   #Ohm
    Rs=slope*w  #Ohm/square
    Lt=intercept/(2*slope)  #m
    rho=(Lt**2)*Rs  #Ohm*m^2
    rho2=Lt*w*Rc
    print ("Contact Resistance=%.4f Ohm,Sheet Resistance=%.5f Ohm/sqr, Effective Transfer Length=%.4f cm, Resistivity=%f Ohm*cm^2,Resistivity second method=%f ohm*cm^2, slope=%.4f Ohm/m, y-intercept=%.2f Ohm"%
           (Rc,Rs,Lt*10**2,rho*10**4,rho2*10**4,slope,intercept))
    plt.plot(L,resistance_list,marker='o',ls='none',mec='r',mfc='r',ms=4,label='measured data')
    plt.plot(L,lin_fit(L,slope,intercept),ls='-',label='liner fitting')
    plt.errorbar(L,resistance_list,yerr=uncertainties[1],ls='none',label='uncertainty')
    
    plt.text(0.010,24.5,"Sheet Resistance=%.5f Ohm/sqr"%(Rs),bbox=dict(facecolor='blue',alpha=0.3))
    plt.text(0.010,30,"Contact Resistance=%f Ohm"%(Rc), bbox=dict(facecolor='blue', alpha=0.3))    
    plt.text(0.010,35.5, "Effective Transfer Length=%f cm"%(Lt*10**2), bbox=dict(facecolor='blue', alpha=0.3))
    plt.text(0.010,40.5,"Resistivity=%f Ohm*cm^2"%(rho*10**4), bbox=dict(facecolor='blue', alpha=0.3))
    plt.text(0.010,45.5, "slope=%.4f Ohm/m"%(slope), bbox=dict(facecolor='blue', alpha=0.3))
    plt.text(0.010,50.5, "y-intercept=%.2f Ohm"%(intercept), bbox=dict(facecolor='blue', alpha=0.3))
    plt.legend()
    plt.show()
    
    import pandas as pd
    from datetime import datetime
    now= datetime.now()
    output_data_list = resistance_list
    output_data_list.append(Rc)
    output_data_list.append(Rs)
    output_data_list.append(Lt)
    output_data_list.append(rho)
    dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
    output_data_list.append(dt_string)
    output_data_list.append(sequential)
    df = pd.read_csv("PostExpo.csv") #User-defined file designation. Input your file name 
    df.loc[len(df)] = output_data_list
    df.to_csv("PostExpo.csv",index=False)
    
        
        
        

if __name__ == '__main__':
    
    sequential = input("Type in the sequential:") # cell number
    Keithley_GPIB_Addr = input ("Input Keithley_GPIB_Address:")

    CurrentCompliance = 1.0e-6    # compliance (max) current
    VoltageCompliance = 20   # compliance (max) current

    start = input ("Current sweep starting point (lower point):")     # starting value of Voltage sweep
    stop = input ("Current sweep stopping point (upper point):")      # ending value
    numpoints = input ("Current sweep number of points:")  # number of points in sweep
    
    a=("y")
    b=input ("This program is designed for WINDOWS/MAC as NI-488.2 supports only Scientific linux, Redhat, CentOS, and SUSE Linux distributions. Do you agree to proceed? (y/n):")
    if a==b:
        
        print ("Check the Arduino commnunication port for different drives. Primary address is COM3. If not compatible, change the board address in the source file")
        main()
        
    else:
        print ("Download NI-488.2 for corresponding Linux distribution, and switch corresponding Arduino communication port")