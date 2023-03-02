#Developed using code provided by Thorlabs' github page.  Thank you to the wonderful software team for making their application so accessible!
import ctypes
import os
from datetime import datetime
from ctypes import cdll,c_long, c_ulong, c_uint32,byref,create_string_buffer,c_bool,c_char_p,c_int,c_int16,c_double, sizeof, c_voidp
from TLPM import TLPM
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
def TFlor_sam(lower_l, upper_l,direction, resolution, autorang, unit, verbose):
    '(Integer, integer, string, integer, bool, string, bool)' '->' 'Dataframe, csv, png'
    #Connect to device
    tlPM = TLPM()
    deviceCount = c_uint32()
    tlPM.findRsrc(byref(deviceCount))

    print("Number of found devices: " + str(deviceCount.value))
    print("")

    resourceName = create_string_buffer(1024)

    for i in range(0, deviceCount.value):
        tlPM.getRsrcName(c_int(i), resourceName)
        print("Resource name of device", i, ":", c_char_p(resourceName.raw).value)
    print("")
    tlPM.close()

    # Connect to last device.
    tlPM = TLPM()
    tlPM.open(resourceName, c_bool(True), c_bool(True))

    message = create_string_buffer(1024)
    tlPM.getCalibrationMsg(message)
    print("Connected to device", i)
    print("Last calibration date: ",c_char_p(message.raw).value)
    print("")

    time.sleep(1)
    
    #User name input
    name=input('Please name this sample')
    
    #Arrays for zeroing spectrum
    zero_spec=[]
    zero_power=[]
    
    #Non-wavelength settings
    #Enable auto-range mode.
    if autorang==True:
        auto=1
    if autorang==False:
        auto=0
    tlPM.setPowerAutoRange(c_int16(auto))
    
    # Set power unit
    if unit=='Watt':
        un=0
    if unit=='dBm':
        un=1
    tlPM.setPowerUnit(c_int16(un))
    
    #Wavelength directionality
    if direction=='hightolow':
        wavelength_range=reversed(range(lower_l,upper_l,resolution))
    if direction=='lowtohigh':
        wavelength_range=range(lower_l,upper_l,resolution)
    
    #Loop of power measurement
    for i in wavelength_range:
        wavelength=c_double(i)
        tlPM.setWavelength(wavelength)
        zero_spec.append(i)

        #take the power
        power =  c_double()
        tlPM.measPower(byref(power))
        zero_power.append(power.value)
            
        #print the power and wavelength being collected
        if verbose == True:
            print(power.value, "W", ':', i , 'nm')

        time.sleep(0.5)
    print("")

    #Writing data to pandas dataframe
    d={'Wavelength(nm)':zero_spec, 'Power(W)':zero_power}
    dat=pd.DataFrame(data=d)
    dat.to_csv(str(name)+'.csv')
