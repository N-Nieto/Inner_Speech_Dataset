# -*- coding: utf-8 -*-

"""
@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Data processing
"""
# In[]
def Calculate_power_windowed(signal_data, fc, window_len, window_step, t_min, t_max):
    # imports
    import scipy as sp
    import numpy as np

    # Signal crop in time
    initial_sample=round(t_min*fc)
    Last_sample= round(t_max*fc)
    
    # Window parameters
    FC_window_len = round(fc*window_len)
    FC_window_step = round(fc*window_step)  
    
    # Initializations
    power=[]
    final_sample=0
    n_vent=0
    
    # Main loop
    while final_sample<=Last_sample:
        
        final_sample= initial_sample + FC_window_len 
    
        # window signal
        signal_cut= signal_data[initial_sample:final_sample]
        
        # Calculate the energy of the window signal
        pwr = sp.sum(signal_cut**2, 0)/signal_cut.size
    
        # actualizate new initial sample for next
        initial_sample=initial_sample+ FC_window_step
  
        power = np.append(power,pwr)
        n_vent = n_vent+1
        
    m_power = np.mean(power)
    std_power = np.std(power)
    
    return m_power , std_power

# In[]
def Select_time_window(X,t_start=1,t_end=2.5,fs=254):
    import numpy as np
    
    # Delet the pre interval
    X = np.delete(X,range(round(t_start*fs)),axis=2)
    
    t_max=X.shape[2]
    
    # Delet the post interval
    X = np.delete(X,range(round(t_end*fs-t_start*fs),t_max),axis=2)
    
    return X

# In[]
def Filter_by_condition(X, Y, Condition):

    if Condition == 'All' or Condition == 'all':
        X = X
        Y = Y
    else:
        
        if Condition == "Pron" or Condition == "pron" or Condition == "Pronounced" :
            p = 0
        elif Condition == "In" or Condition == "inner" or Condition == "Inner" :
            p = 1
        elif Condition == "Vis" or Condition == "vis" or Condition == "Visualized":
            p = 2
            
        X=X[Y[:,2]==p]
        Y=Y[Y[:,2]==p]   
        
    return X , Y

# In[]
def Transform_for_classificator (X,Y,Class):
    import numpy as np
    
    if Class == ['All'] or Class == ['all']:
        X_data2 = X
        Y_data = Y
        
    else: 
        N_class = len(Class)
        Y_data = []
        X_data = dict()
        X_data2 = []
        
        for N_c in range(N_class):
            
            if Class[N_c] == "up" or Class[N_c] == "Up" or Class[N_c] =="Arriba " or Class[N_c] ==" arriba":
                cl = 0
            elif Class[N_c] == "down" or Class[N_c] == "Down" or Class[N_c] == "Abajo" or Class[N_c] == "abajo":
                cl = 1
            elif Class[N_c] == "right" or Class[N_c] == "Right" or Class[N_c] == "Derecha" or Class[N_c] == "derecha":
                cl = 2
            elif Class[N_c] == "left" or Class[N_c] == "Left" or Class[N_c] == "Izquierda" or Class[N_c] == "izquierda":
                cl = 3
            else:
                print("Invalid class")
                
           # Apilate the selected data
            X_data[N_c]= X[Y[:,1]==cl]        
          
        """ TODO: more eficient way to do this
        """
        if N_class== 1:
            X_data2 = X_data[0]
            Y_data = np.zeros(X_data[0].shape[0])
            
        elif N_class == 2:
                
            X_data2 = np.vstack((X_data[0],X_data[1]))
            
            Label_0 = np.zeros(X_data[0].shape[0])
            Label_1 = np.ones(X_data[1].shape[0])
            
            Y_data = np.hstack((Label_0,Label_1))  
            
        elif N_class == 3:
            
            X_data2=np.vstack((X_data[0],X_data[1],X_data[2]))   
    
            Label_0 = np.zeros(X_data[0].shape[0])
            Label_1 = np.ones(X_data[1].shape[0])
            Label_2 = 2*np.ones(X_data[2].shape[0])
            
            Y_data=np.hstack((Label_0,Label_1,Label_2))  
            
        elif N_class== 4:
            
            X_data2=np.vstack((X_data[0],X_data[1],X_data[2],X_data[3]))
            
            Label_0 = np.zeros(X_data[0].shape[0])
            Label_1 = np.ones(X_data[1].shape[0])
            Label_2 = 2*np.ones(X_data[2].shape[0])
            Label_3 = 3*np.ones(X_data[3].shape[0])
            
            Y_data=np.hstack((Label_0,Label_1,Label_2,Label_3))  
        
    return X_data2 , Y_data


# In[]
def Average_in_frec(power, frec, bands):
    import numpy as np
    
    N_bands = len(bands)

    for N_B in range(N_bands):
        
        f_min, f_max = bands[N_B]
        
        index1= frec>f_min 
        index2= frec<f_max
        index= index1* index2
        
        pow_select= power[:,index,:]
        
        power_band= np.average(pow_select,axis=1)
        power_band= np.reshape(power_band,(power_band.shape[0],1,power_band.shape[1]))
        
        if N_B==0:    
            power_bands=power_band
        else:
            power_bands=np.hstack((power_bands,power_band))
            
    return power_bands
        
# In[]
def Filter_by_class (X,Y,Class):
    
    if Class == 'All' or Class == 'all':
        X_data = X
        Y_data = Y
        
    else: 

        if Class == "up" or Class == "Up" or Class =="Arriba " or Class ==" arriba":
            cl = 0
        elif Class == "down" or Class == "Down" or Class == "Abajo" or Class == "abajo":
            cl = 1
        elif Class == "right" or Class == "Right" or Class == "Derecha" or Class == "derecha":
            cl = 2
        elif Class == "left" or Class == "Left" or Class == "Izquierda" or Class == "izquierda":
            cl = 3
        else:
            print("Invalid class")
                
        # Apilate the selected data
        X_data = X[Y[:,1]==cl]        
        Y_data = Y[Y[:,1]==cl]   
            
    return X_data , Y_data
    
    
