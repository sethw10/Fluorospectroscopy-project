#!/usr/bin/env python
# coding: utf-8

# In[1]:


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
        
        #stabilize reading
        time.sleep(1)
        
        #take the power
        power =  c_double()
        tlPM.measPower(byref(power))
        zero_power.append(power.value)
            
        #print the power and wavelength being collected
        if verbose == True:
            print(power.value, "W", ':', i , 'nm')

    print("")

    #Writing data to pandas dataframe
    d={'Wavelength(nm)':zero_spec, 'Power(W)':zero_power}
    dat=pd.DataFrame(data=d)
    dat.to_csv(str(name)+'.csv')
    
def TFlor_measure(wavelength_input, num_scans, autorang, unit):
    'Int/float, int, boolean, string'-->'pandas dataframe'
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

    #Connect to last device.
    tlPM = TLPM()
    tlPM.open(resourceName, c_bool(True), c_bool(True))

    message = create_string_buffer(1024)
    tlPM.getCalibrationMsg(message)
    print("Connected to device", i)
    print("Last calibration date: ",c_char_p(message.raw).value)
    print("")

    time.sleep(1)
    
    #Device settings

    #Enable auto-range mode.
    if autorang==True:
        auto=1
    if autorang==False:
        auto=0
    tlPM.setPowerAutoRange(c_int16(auto))
    
    #Set power unit
    if unit=='Watt':
        un=0
    if unit=='dBm':
        un=1
    tlPM.setPowerUnit(c_int16(un))
    
    #Set Wavelength
    wavelength=c_double(wavelength_input) #Ctypes junk that makes program work.
    tlPM.setWavelength(wavelength) #Sets measurement wavelength on PMD100.
    
    #stabilize reading
    time.sleep(1) #Time waiting for reading stabilization at wavelength.

    #Collect power data, run statistical calculations on it
    counter=0
    power_average=[]
    spectrum=[]
    error=[]
    
    temp_list=[]
    while counter<num_scans:
        power =  c_double() #ctypes junk for sake of making program work
        tlPM.measPower(byref(power)) #Measures power for wavelength
        temp_list.append(power.value) #Appends measured value to temporary list
        time.sleep(0.25) #Waits 0.25 seconds to take another measurement
        counter=counter+1 #Ups the counter
        
    average_power=np.average(temp_list) #Takes average of the power measurements made in while loop.
    power_average.append(average_power) #Appends average power value to list.
    stdev=np.std(temp_list) #Takes standard deviation of power measurements made.
    error.append(stdev) #Appends standard deviation to list.
    print('Average Power: '+str(average_power)+' ± ' +str(stdev) + ' '+str(unit))
    print('Measurements taken, statistics run, closing program')
    tlPM.close()
    
    #Writing data to pandas dataframe
    d={'Wavelength(nm)':wavelength_input, 'Average Power(W)':power_average, 'Stdev(W)':error} #Sets up dictionary for pd.DataFrame creation
    dat=pd.DataFrame(data=d) #creates pd.DataFrame for collected data
    name=input('What would you like to name this dataframe?: ')
    dat.to_csv(name+'.csv', index=False)

    
def spect_an(name, smoothing, sensitivity):
    #Data import
    data=pd.read_csv(str(name)+'.csv')

    #Data normalization
    data['Normalized Power(W)']=(data['Power(W)']/data['Power(W)'].max())
    
    #Peak analysis
    from numpy import diff
    from scipy.signal import lfilter,find_peaks
    
    #Dataset smoothing
    n_1=int(smoothing)
    n_2=int(smoothing)
    b=[1.0/n_1]*n_1
    a=1
    g=[1.0/n_2]*n_2
    yx=lfilter(b, a, data['Normalized Power(W)'])
    
    #First Derivative
    dP=diff(yx)
    dep=np.append([0],dP)
    data['dP(W)']=dep
    yy=lfilter(b,a,dep)

    #Peak finding
    peaks=find_peaks(yx, height=0, prominence=float(sensitivity))

    indexes=peaks[0]
    peakz=peaks[1]
    ah=pd.DataFrame(data=peakz)
    ah['peak_index']=indexes
    index=[]
    wavelength_index=[]
    ing=data['Wavelength(nm)']
    for i in indexes:
        wavelength_index.append(ing.loc[i])
        wavs=pd.DataFrame(data=wavelength_index)
        Wavelengths=wavs.rename(columns={0:'Wavelength(nm)'})
        
    ah['Wavelength(nm)']=wavelength_index

    #Graphing
    j=yx
    i=yy
    h=data['Wavelength(nm)']
    l=ah['Wavelength(nm)']
    k=ah['peak_heights']       
    m=dep

    fig, (ax, ay)=plt.subplots(1,2, figsize=(20,5))
    ax.plot(h,yx)
    ax.scatter(l,k, c='b')
    ax.set_xlabel('Wavelength(nm)')
    ax.set_ylabel('Normalized Power(W)')
    ax.set_title('Normalized Power(W) Fluorescence Spectrum of '+name) #insert naming capability here

    ay.plot(data['Wavelength(nm)'],yy)
    ay.set_xlabel('Wavelength(nm)')
    ay.set_ylabel('dP(W)')
    ay.set_title('dP versus Wavelength(nm) of '+name) #insert naming capability here
    
    plt.savefig(name, dpi=400)
    #Save peak data
    ding=ah.rename(columns={'peak_heights':'Peak Power(W)','Wavelength(nm)':'Peak Wavelength(nm)'})
    bing=ding.drop(['prominences', 'left_bases', 'right_bases', 'peak_index'], axis=1)
    bing.to_csv(name+'_peaks.csv')
    display(bing)
    
   

