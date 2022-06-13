# -*- coding: utf-8 -*-

"""
@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Data processing
"""
# Imports
import scipy as sp
import numpy as np

# In[]
def Calculate_power_windowed(signal_data, fc, window_len, window_step, t_min, t_max):
    

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
def Select_time_window(X,t_start=1, t_end=2.5, fs=256):
    
    t_max=X.shape[2]
    start = max(round(t_start * fs), 0)
    end = min(round(t_end * fs), t_max)

    #Copy interval
    X = X[:, :, start:end]
    return X

# In[]
def Filter_by_condition(X, Y, condition):
    if not condition:
        raise Exception("You have to select the conditions!")

    if condition.upper() == "ALL":
        return X, Y
    else:
        X_r = []
        Y_r = []
        if condition.upper() == "PRON" or condition.upper() == "PRONOUNCED":
            p = 0
        elif condition.upper() == "IN" or condition.upper() == "INNER":
            p = 1
        elif condition.upper() == "VIS" or condition.upper() == "VISUALIZED":
            p = 2
        else:
          raise Exception("The condition " + condition + " doesn't exist!")

        X_r = X[Y[:,2] == p]
        Y_r = Y[Y[:,2] == p]

    return X_r, Y_r

# In[]

def Transform_for_classificator (X, Y, Classes, Conditions):

    N_grups_cnd = len(Conditions[:])
    N_grups_cls = len(Classes[:])

    if(N_grups_cnd < 1 or N_grups_cls <1):
        raise Exception("You have to select classes and conditions")

    if N_grups_cnd != N_grups_cls:
        raise Exception("Incorrect number of conditions or classses")

    for N_gr in range(N_grups_cnd):

        N_ind_cond = len(Conditions[N_gr])
        N_ind_clas = len(Classes[N_gr])

        if(N_ind_cond < 1 or N_ind_clas <1):
            raise Exception("You have to select classes for each conditions")

        if N_ind_cond != N_ind_clas:
            raise Exception("Incorrect number of conditions or classses")

        for N_ind in range(N_ind_clas): 

            Cond = Conditions[N_gr][N_ind]
            Class = Classes[N_gr][N_ind]
            try:
                X_aux , Y_aux = Filter_by_condition(X,Y,Cond)
                X_aux , Y_aux =  Filter_by_class(X_aux,Y_aux,Class)
            except Exception as ex:
                raise ex

            if N_ind == 0 and N_gr == 0:
                X_final = X_aux
                Y_final = N_gr*(np.ones(len(Y_aux)))
            else:
                X_final = np.vstack([X_final, X_aux])
                Y_final = np.hstack([Y_final, N_gr*(np.ones(len(Y_aux)))])

    return X_final, Y_final


# In[]
def Average_in_frec(power, frec, bands):
    
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
def Filter_by_class (X, Y, class_condition):
    if not class_condition:
        raise Exception("You have to select the classes for each condition!")

    if class_condition.upper() == "ALL":
        return X, Y
    else:
        X_r = []
        Y_r = []
        if class_condition.upper() == "UP" or class_condition.upper() == "ARRIBA":
          p = 0
        elif class_condition.upper() == "DOWN" or class_condition.upper() == "ABAJO":
          p = 1
        elif class_condition.upper() == "RIGHT" or class_condition.upper() == "DERECHA":
          p = 2
        elif class_condition.upper() == "LEFT" or class_condition.upper() == "IZQUIERDA":
          p = 3
        else:
          raise Exception("The class " + class_condition + " doesn't exist!")

        X_r = X[Y[:,1] == p]
        Y_r = Y[Y[:,1] == p]

    return X_r , Y_r


def Split_trial_in_time(X, Y, window_len, window_step, fs):
      
    print("Input X shape: ",X.shape)
    N_Trials,n_chanels,t_max=X.shape

    
    # Window parameters
    FC_window_len = round(fs*window_len)
    FC_window_step = round(fs*window_step)

    #split sections
    split_section = int(t_max//FC_window_len)
    
    #if there is a remainder, just drop it
    remainder = t_max % split_section
    
    if(remainder != 0):
      X = X[:,:,:-remainder]
    
    ################################################

    # Initializations
    X_final=[]
    #Set labels
    Y_final=np.repeat(Y, split_section, axis=0)
    
    # Main loop
    for N_tr in range(N_Trials):
        X_t = X[N_tr,:,:]
        X_t = np.split(X_t, split_section, axis=1)
        X_t = np.array(X_t)
        if (len(X_final) == 0):
          X_final = X_t
        else:
          X_final = np.vstack([X_final, X_t])

    print("Output X shape: ",X_final.shape)
    return X_final, Y_final

    
    
