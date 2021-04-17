# -*- coding: utf-8 -*-

"""
Created on Thu Mar 26 16:37:48 2020

@author: Nicolás Nieto

Description:
    This code automatically tags trials by EMG artifacts
"""


def EMG_control_single_th(root_dir,N_Subj_arr,N_block_arr,low_f,high_f,t_min,t_max,window_len,window_step,std_times,t_min_baseline,t_max_baseline,tag_events=False,verbose=False):
    """
    Parameters
    ----------
    root_dir : str
        Processed data direction
    N_Subj_arr : array
        array with subjects to perform the control
    N_block_arr : array
        array with block to perform the control
    low_f : float
        Low Frecuency cut off.
    high_f : float
        High Frecuency cut off.
    t_min : float
        Initial time to consider in the trials
    t_max : float
        Final time to consider in the trials
    window_len : float
        window length considered in the analisys.
    window_step : float
        step time the window moves.
    std_times : float/int
        Number of times that std is sum in the threshold method.
    t_min_baseline : TYPE
        Initial time to consider in the Baselines
    t_max_baseline : TYPE
        Final time to consider in the Baseline
    tag_events : bool, optional
    TODO:
        Add a column in the events with the EMG control information. Usefull for
        further filtering the contaminated trials.
        Add 0 if the trial is not contaminated
        Add 1 if the trial is  contaminated
        The default is False.
    verbose : bool, optional
        The default is False.

    Returns
    -------
    None

    """
    
    # Imports
    import numpy as np
    import pickle
    from Data_processing import  Calculate_power_windowed
    from Data_extractions import  Extract_block_data_from_subject, Extract_report

    # Trials of Pronounced condition are excluded in the EMG control
    Pronunced_id=0
        
    # In[]
    # Subjets
    for N_S in N_Subj_arr:
        if N_S<10:
            Num_s = 'sub-0' + str(N_S)
        else:
            Num_s = 'sub-' + str(N_S)
            
        # Blocks
        for N_B in N_block_arr:
            #Load baseline data
            datatype = "Baseline"
            X_baseline , Y = Extract_block_data_from_subject(root_dir, N_S, datatype, N_B)

            X_baseline.filter(low_f,high_f)

            FC=int(X_baseline.info['sfreq'])
# =============================================================================
# =============================================================================
            # EXG7 Control
            Baseline = X_baseline.copy()
            # Select only EMG 1 channels
            Baseline = Baseline.pick_channels(["EXG7"])
            # Extract data
            Channel_filter = Baseline.get_data()
            Channel_filter = Channel_filter[0,0,:]
            # Rectified signal
            Channel_filter = np.abs(Channel_filter)
            # Calculate mean and std for channel 7
            mean_Base_energy_7 , std_Base_energy_7 = Calculate_power_windowed(Channel_filter, FC, window_len, 
                                                                               window_step, t_min_baseline, 
                                                                               t_max_baseline)
# =============================================================================   
            # EXG7 Control
            Baseline = X_baseline.copy()
            Baseline.pick_channels(["EXG8"])
            # Extract data
            Channel_filter = Baseline.get_data()
            Channel_filter = Channel_filter[0,0,:]
            # Rectified signal
            Channel_filter = np.abs(Channel_filter)

            # Calculate mean and std for channel 8
            mean_Base_energy_8 , std_Base_energy_8 = Calculate_power_windowed(Channel_filter, FC, window_len,
                                                                               window_step, t_min_baseline,
                                                                               t_max_baseline)
            del Baseline, X_baseline
# =============================================================================
# =============================================================================
            #Load EOG and EMG data
            datatype = "EXG"
            EMG , Y = Extract_block_data_from_subject(root_dir, N_S, datatype, N_B)

            #Filter in the same band
            EMG.filter(low_f,high_f)
   
            #Copy data
            EMG_EXG7 = EMG.copy()
            EMG_EXG8 = EMG.copy()

            # Select channel
            EMG_EXG7.pick_channels(["EXG7"])
            # Extract data
            EMG_data_EXG7 = EMG_EXG7.get_data()
            EMG_data_EXG7 = np.abs(EMG_data_EXG7)
            # Select channel
            EMG_EXG8.pick_channels(["EXG8"])
             # Extract data
            EMG_data_EXG8 = EMG_EXG8.get_data()
            EMG_data_EXG8 = np.abs(EMG_data_EXG8)
            
            # Initialized the taggin vector
            EMG_reject = np.zeros(EMG._data.shape[0])   
            del EMG , EMG_EXG7 , EMG_EXG8
# =============================================================================
            # In[]: Tagging
            # Initialization
            drop_epoched = []
            trial_power_7 = []
            trial_power_8 = []
    
            # Get number of trials
            Trials, Channels, samples = EMG_data_EXG8.shape
            
            # Calculated the threshold for anotated the trial
            threshold_7 = mean_Base_energy_7 + (std_times * std_Base_energy_7)
            threshold_8 = mean_Base_energy_8 + (std_times * std_Base_energy_8)

            for n_trial in range(Trials):
                
                # Get trial
                Channel_filter=EMG_data_EXG7[n_trial,0,:]
                # Calculate power for channel EXG7
                mean_Trial_Energy_7 , std_trial_energy_7 = Calculate_power_windowed(Channel_filter, FC, window_len,
                                                                                     window_step, t_min, t_max)

                # Get trial
                Channel_filter=EMG_data_EXG8[n_trial,0,:]
                # Calculate power for channel EXG8
                mean_Trial_Energy_8 , std_trial_energy_8 = Calculate_power_windowed(Channel_filter, FC, window_len, 
                                                                                     window_step, t_min, t_max)
          
                # Threshold condition
                if (mean_Trial_Energy_8>threshold_8 or mean_Trial_Energy_7>threshold_7):
                    
                    # mark only if is not Pronounced trials  
                    if not(Y[n_trial,2] == Pronunced_id):

                        trial_power_7 = np.append(trial_power_7,mean_Trial_Energy_7)
                        trial_power_8 = np.append(trial_power_8,mean_Trial_Energy_8)
                        drop_epoched = np.append(drop_epoched,n_trial)
                        EMG_reject[n_trial] = 1
                        
                        if verbose:
                            print ("Warnign at trial", n_trial+1)

            # In[]: Update Report
            R_EMG = np.vstack([drop_epoched,trial_power_7,trial_power_8])
            R_EMG = np.transpose(R_EMG)
            
            print('Tagged Trials: '+str(len(R_EMG)),'for Subject ' +str(N_S)+' in Session '+str(N_B))
            
            # Update Report
            report = Extract_report(root_dir,N_B,N_S)
            
            report['EMG_trials'] = R_EMG[:,0]
            report['Power_EXG7'] = R_EMG[:,1]
            report['Power_EXG8'] = R_EMG[:,2]
    
            report['Baseline_EXG7_mean'] = mean_Base_energy_7
            report['Baseline_EXG8_mean'] = mean_Base_energy_8

            report['Baseline_EXG7_std'] = std_Base_energy_7
            report['Baseline_EXG8_std'] = std_Base_energy_8
            
            # Save report
            file_name = root_dir + 'derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_report.pkl'
            with open(file_name, 'wb') as output:
                pickle.dump(report, output, pickle.HIGHEST_PROTOCOL)
                
    print("EMG Control Done")