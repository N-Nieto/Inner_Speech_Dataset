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
def Select_time_window(X,t_start=1, t_end=2.5, fs=256):
    import numpy as np
    
    t_max=X.shape[2]
    start = max(round(t_start * fs), 0)
    end = min(round(t_end * fs), t_max)

    #Copy interval
    X = X[:, :, start:end]
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

def Transform_for_classificator (X,Y,Classes,Conditions):
    import numpy as np
    
    N_grups_cl = len(Conditions[:])
    N_grups_cond = len(Classes[:])
  
    if N_grups_cl != N_grups_cond:
      raise Exception("Incorrect number of conditions or classses")
      
    for N_gr in range(N_grups_cl):

      N_ind_cond = len(Conditions[N_gr])
      N_ind_clas = len(Classes[N_gr])

      if N_ind_cond != N_ind_clas:
          raise Exception("Incorrect number of conditions or classses")

      for N_ind in range(N_ind_clas): 

          Cond = Conditions[N_gr][N_ind]
          Class = Classes[N_gr][N_ind]

          X_aux , Y_aux = Filter_by_condition(X,Y,Cond)
          X_aux , Y_aux =  Filter_by_class(X_aux,Y_aux,Class)

          if N_ind == 0 and N_gr == 0:
              X_final = X_aux
              Y_final = N_gr*(np.ones(len(Y_aux)))
          else:
              X_final = np.vstack([X_final, X_aux])
              Y_final = np.hstack([Y_final, N_gr*(np.ones(len(Y_aux)))])


    return X_final, Y_final


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


def Split_trial_in_time(X, Y, window_len, window_step, fs):

    import numpy as np
    
    
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

    
    
