'''
Created by Neil Wang, yxw1300@case.edu
Physics Departmen at Case Western Reserve University
'''

import pyvisa  # PyVISA module, for GPIB comms
import time  # to allow pause between measurements
import os  # Filesystem manipulation - mkdir, paths etc.
import numpy as np    # enable NumPy numerical analysis
import matplotlib.pyplot as plt  # for python-style plottting, like 'ax1.plot(x,y)'
import test

SaveFiles = True   # Save the plot & data?  Only display if False.


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
    keithley.write(":SOUR:FUNC:MODE VOLT")
    #keithley.write(":SYST:RESN ON")#Eabling 4-wire
    #keithley.write(":SENS:FUNC 'CURR:DC' ")
    keithley.write(":SENS:FUNC:CONC OFF")
    keithley.write(":SENS:FUNC 'RES'")
    keithley.write(":SENS:RES:MODE AUTO")
    #keithley.write(":SENS:VOLT:PROT 10")
    keithley.write(":SYST:RSEN ON")
    keithley.write(":SENS:CURR:PROT:LEV " + str(CurrentCompliance))
    #keithley.write(":SENS:CURR:RANGE:AUTO 1")   # set current reading range to auto (boolean)
    keithley.write(":OUTP ON")                    # Output on    


    # Loop to sweep voltage
    Voltage=[]
    Current = []
    Resistance=[]
    for V in np.linspace(int(start), int(stop), num=int(numpoints), endpoint=True):
    #Voltage.append(V)
        print("Voltage set to: " + str(V) + " V" )
        keithley.write(":SOUR:VOLT " + str(V))
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

        ###### Plot #####
        #V=np.linspace(start,stop,numpoints)
        #plt.figure(figsize=(10,8))
        #plt.plot(V,Resistance,ls='-',marker='o',ms=4)
        #plt.xlabel('Voltage (V)')
        #plt.ylabel('Resistance (Ohm)')
        #plt.title(DevName)
      #  R_mean=np.mean(Resistance)

import pyfirmata
from pyfirmata import ArduinoDue
from pyfirmata import INPUT,OUTPUT,PWM
import scipy.optimize as opt

def lin_fit(x,k,b):
    y=k*x+b
    return y

def main():
    
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
    for i in range(15,-1, -2):
        i_pin_name = "d:" + str(i + 23) + ":o" # Create current pin name, example: d:12:o is equal to pin 12 out
        v_pin_name = "d:" + str(i + 23 + 1) + ":o" # create voltage pin name, just 1 more than current pin
        i_pin = board.get_pin(i_pin_name)
        v_pin = board.get_pin(v_pin_name)
        i_pin.write(1)
        v_pin.write(1)
        i_pin_list.append(i_pin)
        v_pin_list.append(v_pin)
    resistivity_list = []
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
            resistivity_list.append(resistance)
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

    L=np.arange (0.002,0.018,0.002)
    plt.figure(figsize=(10,8))

    plt.xlabel('Distance (m)')
    plt.ylabel(r"Resistance $\Omega$")

    popt,pcov=opt.curve_fit(lin_fit,L,resistivity_list)
    uncertainties = [np.sqrt(pcov[i][i]) for i in range(len(pcov))]
    slope=popt[0]
    intercept=popt[1]
    w=1e-2
    Rc=intercept/2
    Lt=intercept/(2*slope)
    rho=Lt*Rc*w
    print ("Contact Resistance=%.4f Ohm, Effective Transfer Length=%.4f cm, Resistivity=%f Ohm*cm^2, slope=%.4f Ohm/m, y-intercept=%.2f Ohm"%(Rc,Lt*10**2,rho*10**4,slope,intercept))
    plt.plot(L,resistivity_list,marker='o',ls='none',mec='r',mfc='r',ms=4,label='measured data')
    plt.plot(L,lin_fit(L,slope,intercept),ls='-',label='liner fitting')
    plt.errorbar(L,resistivity_list,yerr=uncertainties[1],ls='none',label='uncertainty')
    
    plt.text(0.010,30,"Contact Resistance=%f Ohm"%(Rc), bbox=dict(facecolor='blue', alpha=0.3))    
    plt.text(0.010,35.5, "Effective Transfer Length=%f cm"%(Lt*10**2), bbox=dict(facecolor='blue', alpha=0.3))
    plt.text(0.010,40.5,"Resistivity=%f Ohm*cm^2"%(rho*10**4), bbox=dict(facecolor='blue', alpha=0.3))
    plt.text(0.010,45.5, "slope=%.4f Ohm/m"%(slope), bbox=dict(facecolor='blue', alpha=0.3))
    plt.text(0.010,50.5, "y-intercept=%.2f Ohm"%(intercept), bbox=dict(facecolor='blue', alpha=0.3))
    plt.legend()
    plt.show()
    

    '''
    if SaveFiles:
   # create subfolder if needed:
        if not os.path.isdir(DevName): os.mkdir(DevName)
        curtime = time.strftime('%Y-%M-%d_%H%M.%S')
        SavePath = os.path.join(DevName, 'R-L Curve - ' + DevName + ' - [' + curtime +']' )
        plt.savefig(  SavePath + '.png'  )

        data = np.array(  zip(L, resistivity_list, slope, )  )
        np.savetxt( SavePath + '.txt', data, fmt="%e", delimiter="\t", header="Distance(m)\tResistivity (Ohm/m)" )
    '''


if __name__ == '__main__':
    
    DevName = input("Type in the file name:") # will be inserted into filename of saved plot
    Keithley_GPIB_Addr = input ("Input Keithley_GPIB_Address:")

    CurrentCompliance = 1.0e-6    # compliance (max) current
    start = input ("Voltage sweep starting point (lower point):")     # starting value of Voltage sweep
    stop = input ("Voltage sweep stopping point (upper point):")      # ending value
    numpoints = input ("Voltage sweep number of points:")  # number of points in sweep
    
    a=("y")
    b=input ("This program is designed for WINDOWS/MAC as NI-488.2 supports only Scientific linux, Redhat, CentOS, and SUSE Linux distributions. Do you agree to proceed? (y/n):")
    if a==b:
        
        print ("Check the Arduino commnunication port for different drives. Primary address is COM3. If not compatible, change the board address in the source file")
        main()
        
    else:
        print ("Download NI-488.2 for corresponding Linux distribution, and switch corresponding Arduino communication port")
