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

