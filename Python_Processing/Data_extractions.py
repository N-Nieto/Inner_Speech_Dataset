# -*- coding: utf-8 -*-

"""
@author: Nieto Nicolás
@email: nnieto@sinc.unl.edu.ar

Utilitys from extract, read and load data from Inner Speech Dataset
"""
            
import mne
import gc
import numpy as np
from Inner_Speech_Dataset.Python_Processing.Utilitys import sub_name , unify_names
import pickle
def Extract_subject_from_BDF(root_dir,N_S,N_B):

    # name correction if N_Subj is less than 10
    Num_s = sub_name(N_S)
    
    #  load data
    file_name = root_dir + '/' + Num_s + '/ses-0'+ str(N_B) +'/eeg/' +Num_s+'_ses-0'+str(N_B)+'_task-innerspeech_eeg.bdf'
    rawdata = mne.io.read_raw_bdf(input_fname=file_name, preload=True,verbose='WARNING')
    return rawdata , Num_s


def Extract_data_from_subject(root_dir,N_S,datatype):
    
    """
    Load all blocks for one subject and stack the results in X
    """

    data=dict()
    y=dict()
    N_B_arr=[1,2,3]
    
    for N_B in N_B_arr:
        # name correction if N_Subj is less than 10
        Num_s = sub_name(N_S)   
            
        y[N_B] = load_events(root_dir,N_S,N_B)
        
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
            raise Exception("Invalid Datatype")
         
    X = np.vstack((data.get(1),data.get(2),data.get(3))) 
    
    
    Y = np.vstack((y.get(1),y.get(2),y.get(3))) 
    

    return X, Y

def Extract_block_data_from_subject(root_dir,N_S,datatype,N_B):
    """
    Load selected block from one subject
    """


    # Get subject name
    Num_s = sub_name(N_S)
        
    # Get events
    Y = load_events(root_dir,N_S,N_B)
    
    sub_dir = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)
    if datatype == "EEG" or datatype == "eeg":
        #  load EEG data 
        file_name = sub_dir + '_eeg-epo.fif'
        X = mne.read_epochs(file_name,verbose='WARNING')

    elif datatype=="EXG" or datatype=="exg":
        #  load EXG data 
        file_name = sub_dir + '_exg-epo.fif'
        X = mne.read_epochs(file_name,verbose='WARNING')
    
    elif datatype=="Baseline" or datatype=="baseline":
        #  load Baseline data 
        file_name = sub_dir + '_baseline-epo.fif'
        X = mne.read_epochs(file_name,verbose='WARNING')
    
    else:
        raise Exception("Invalid Datatype")
     
    return X, Y

def Extract_report(root_dir,N_B,N_S):


    # Get subject name
    Num_s = sub_name(N_S)
        
    # Save report
    sub_dir = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)
    file_name = sub_dir + '_report.pkl'
    
    with open(file_name, 'rb') as input:
        report = pickle.load(input)

    return report
        

def Extract_TFR(TRF_dir, Cond, Class, TFR_method , TRF_type):


    # Unify names as stored
    Cond, Class = unify_names(Cond, Class)       
    
    fname = TRF_dir + TFR_method + "_" + Cond + "_" + Class + "_"+TRF_type+"-tfr.h5"
    
    TRF = mne.time_frequency.read_tfrs (fname)[0]
    
    return TRF



def Extract_data_multisubject(root_dir, N_S_list, datatype='EEG'):
    """
    Load all blocks for a list of subject and stack the results in X
    """


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
    
            Num_s = sub_name(N_S)

            base_file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B) 
            events_file_name = base_file_name+'_events.dat'
            data_tmp_Y = np.load(events_file_name,allow_pickle=True)
            tmp_list_Y.append(data_tmp_Y)
            print("Inner iteration " , N_B)
            if datatype=="EEG" or datatype=="eeg":
                # load data and events
                eeg_file_name = base_file_name+'_eeg-epo.fif'
                data_tmp_X = mne.read_epochs(eeg_file_name,verbose='WARNING')._data
                rows.append(data_tmp_X.shape[0])
                if S == 0 and N_B == 1: # assume same number of channels, time steps, and column labels in every subject and session
                  chann=data_tmp_X.shape[1]
                  steps=data_tmp_X.shape[2]
                  columns=data_tmp_Y.shape[1]
                tmp_list_X.append(data_tmp_X)

            elif datatype=="EXG" or datatype=="exg":
                exg_file_name = base_file_name+'_exg-epo.fif'
                data_tmp_X = mne.read_epochs(exg_file_name,verbose='WARNING')._data
                rows.append(data_tmp_X.shape[0])
                if S == 0 and N_B == 1:
                  chann=data_tmp_X.shape[1]
                  steps=data_tmp_X.shape[2]
                  columns=data_tmp_Y.shape[1]
                tmp_list_X.append(data_tmp_X)
            
            elif datatype=="Baseline" or datatype=="baseline":
                baseline_file_name = base_file_name+'_baseline-epo.fif'
                data_tmp_X = mne.read_epochs(baseline_file_name,verbose='WARNING')._data
                rows.append(data_tmp_X.shape[0])
                if S == 0 and N_B == 1:
                  chann=data_tmp_X.shape[1]
                  steps=data_tmp_X.shape[2]
                  columns=data_tmp_Y.shape[1]
                tmp_list_X.append(data_tmp_X)
    
            else:
                raise Exception("Invalid Datatype")
                return None, None
        
        S += 1

    X = np.empty((sum(rows), chann, steps))
    Y = np.empty((sum(rows), columns))
    offset = 0
    # put elements of list into numpy array
    for i in range(total_elem):
      print("Saving element {} into array ".format(i))
      X[offset:offset+rows[i],:,:] = tmp_list_X[0]
      if datatype=="EEG" or datatype=="eeg" or datatype=="EXG" or datatype=="exg":
        Y[offset:offset+rows[i],:] = tmp_list_Y[0] # only build Y for the datatypes that uses it
      offset+=rows[i]
      del tmp_list_X[0]
      del tmp_list_Y[0]
      gc.collect()
    print("X shape", X.shape)
    print("Y shape", Y.shape)

    if datatype=="EEG" or datatype=="eeg" or datatype=="EXG" or datatype=="exg":
      # for eeg and exg types, there is a predefined label that is returned
      return X,Y
    else:
      # for baseline datatypes, there's no such label (rest phase)
      return X
  
def load_events(root_dir,N_S,N_B):
    
    Num_s = sub_name(N_S)
    # Create file Name
    file_name =root_dir+"/derivatives/"+Num_s+"/ses-0"+str(N_B)+"/"+Num_s+"_ses-0"+str(N_B)+"_events.dat"
    # Load Events
    events = np.load(file_name,allow_pickle=True)
    
    return events


    