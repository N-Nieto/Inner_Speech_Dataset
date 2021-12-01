# -*- coding: utf-8 -*-

"""
@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Utilitys from extract, read and load data from Inner Speech Dataset
"""
            

def Extract_subject_from_BDF(root_dir,N_S,N_B):
    import mne
    # name correction if N_Subj is less than 10
    if N_S<10:
        Num_s='sub-0'+str(N_S)
    else:
        Num_s='sub-'+str(N_S)
    
    #  load data
    file_name = root_dir + '/' + Num_s + '/ses-0'+ str(N_B) +'/eeg/' +Num_s+'_ses-0'+str(N_B)+'_task-innerspeech_eeg.bdf'
    rawdata = mne.io.read_raw_bdf(input_fname=file_name, preload=True,verbose='WARNING')
    return rawdata , Num_s


def Extract_data_from_subject(root_dir,N_S,datatype):
    
    """
    Load all blocks for one subject and stack the results in X
    """
    import mne
    import numpy as np

    data=dict()
    y=dict()
    N_B_arr=[1,2,3]
    for N_B in N_B_arr:

        # name correction if N_Subj is less than 10
        if N_S<10:
            Num_s='sub-0'+str(N_S)
        else:
            Num_s='sub-'+str(N_S)
            

        file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_events.dat'
        y[N_B] = np.load(file_name,allow_pickle=True)
        
        if datatype=="EEG" or datatype=="eeg":
            #  load data and events
            file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_eeg-epo.fif'
            X= mne.read_epochs(file_name,verbose='WARNING')
            data[N_B]= X._data
            
        elif datatype=="EXG" or datatype=="exg":
            file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_exg-epo.fif'
            X= mne.read_epochs(file_name,verbose='WARNING')
            data[N_B]= X._data
        
        elif datatype=="Baseline" or datatype=="baseline":
            file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_baseline-epo.fif'
            X= mne.read_epochs(file_name,verbose='WARNING')
            data[N_B]= X._data

        else:
            print("Invalid Datatype")
         
    X = np.vstack((data.get(1),data.get(2),data.get(3))) 
    
    
    Y = np.vstack((y.get(1),y.get(2),y.get(3))) 
    

    return X, Y

def Extract_block_data_from_subject(root_dir,N_S,datatype,N_B):
    """
    Load selected block from one subject
    """
    import mne
    import numpy as np

    # name correction if N_Subj is less than 10
    if N_S<10:
        Num_s='sub-0'+str(N_S)
    else:
        Num_s='sub-'+str(N_S)
        
        
    file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_events.dat'
    Y= np.load(file_name,allow_pickle=True)
    
    if datatype=="EEG" or datatype=="eeg":
        #  load data and events
        file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_eeg-epo.fif'
        X= mne.read_epochs(file_name,verbose='WARNING')

    elif datatype=="EXG" or datatype=="exg":
        file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_exg-epo.fif'
        X= mne.read_epochs(file_name,verbose='WARNING')
    
    elif datatype=="Baseline" or datatype=="baseline":
        file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_baseline-epo.fif'
        X= mne.read_epochs(file_name,verbose='WARNING')
    
    else:
        print("Invalid Datatype")
     
    return X, Y

def Extract_report(root_dir,N_B,N_S):
    
    import pickle
    # name correction if N_Subj is less than 10
    if N_S < 10:
        Num_s = 'sub-0'+str(N_S)
    else:
        Num_s = 'sub-'+str(N_S)
        
    # Save report
    file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_report.pkl'
    
    with open(file_name, 'rb') as input:
        report = pickle.load(input)

    return report
        

def Extract_TFR(TRF_dir, Cond, Class, TFR_method , TRF_type):
    import mne
    from Utilitys import unify_names

    # Unify names as stored
    Cond, Class = unify_names(Cond, Class)       
    
    fname = TRF_dir + TFR_method + "_" + Cond + "_" + Class + "_"+TRF_type+"-tfr.h5"
    
    TRF = mne.time_frequency.read_tfrs (fname)[0]
    
    return TRF



def Extract_data_multisubject(root_dir,N_S_list, datatype='EEG'):
    """
    Load all blocks for a list of subject and stack the results in X
    """
    import mne
    import numpy as np
    import gc
        
    N_B_arr = [1,2,3]
    tmp_list_X = []
    tmp_list_Y = []
    rows = []
    total_elem = len(N_S_list)*3 # assume 3 sessions per subject
    S = 0
    for N_S in N_S_list:
        print("Iteration ", S)
        print("Subject ", N_S)
        for N_B in N_B_arr:
    
            # name correction if N_Subj is less than 10
            if N_S<10:
                Num_s='sub-0'+str(N_S)
            else:
                Num_s='sub-'+str(N_S)

            file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_events.dat'
            data_tmp_Y=np.load(file_name,allow_pickle=True)
            tmp_list_Y.append(data_tmp_Y)
            
            if datatype=="EEG" or datatype=="eeg":
                #  load data and events
                file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_eeg-epo.fif'
                print("Inner iteration " , N_B)
                data_tmp_X=mne.read_epochs(file_name,verbose='WARNING')._data
                rows.append(data_tmp_X.shape[0])
                if S == 0: # assume same number of channels, time steps, and column labels in every subject and session
                  chann=data_tmp_X.shape[1]
                  steps=data_tmp_X.shape[2]
                  columns=data_tmp_Y.shape[1]
                tmp_list_X.append(data_tmp_X)
            
            # ToDo improvement not applied to exg and baseline datatypes yet
            elif datatype=="EXG" or datatype=="exg":
                file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_exg-epo.fif'
                X= mne.read_epochs(file_name,verbose='WARNING')
                data[N_B]= X._data
            
            elif datatype=="Baseline" or datatype=="baseline":
                file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_baseline-epo.fif'
                X= mne.read_epochs(file_name,verbose='WARNING')
                data[N_B]= X._data
    
            else:
                print("Invalid Datatype")
        
        S += 1

    X = np.empty((sum(rows), chann, steps))
    Y = np.empty((sum(rows), columns))
    offset = 0
    # put elements of list into numpy array
    for i in range(total_elem):
      print("Saving element into array: ", i)
      X[offset:offset+rows[i],:,:] = tmp_list_X[0]
      Y[offset:offset+rows[i],:] = tmp_list_Y[0]
      offset+=rows[i]
      del tmp_list_X[0]
      del tmp_list_Y[0]
      gc.collect()
    print("X shape", X.shape)
    print("Y shape", Y.shape)
    return X,Y