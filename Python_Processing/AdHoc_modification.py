# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 11:53:54 2020

@author: Nicolás Nieto
@email: nnieto@sinc.unl.edu.ar

Ad hoc correction subject 3:
    
    Subject S03 inform in block 1 he did not realice the inner speech paradigm. 
    Instaed he perform the visualized paradigm.
"""

def adhoc_Subject_3 (root_dir,verbose=True):
    import numpy as np
    Num_s = 'sub-03'
    N_B = 1
    # Load_file    
    file_name = root_dir + '/derivatives/' + Num_s + '/ses-0'+ str(N_B) + '/' +Num_s+'_ses-0'+str(N_B)+'_events.dat'
    Y_S3 = np.load(file_name,allow_pickle=True)
    
    # Correct the 40 trials where the subject executed a different paradigm
    Y_S3[80:120,2]=2
    
    if verbose:
        # Check if only 40 trials of Pronunced had left
        if np.count_nonzero(Y_S3[:,2]==0) == 40 and np.count_nonzero(Y_S3[:,2]==1) == 40 and np.count_nonzero(Y_S3[:,2]==2) == 120:
            print("AdHoc Correction Subject 3 Block 1")
        else:
            raise Exception("Correction fail")   
             
                
    Y_S3.dump(file_name)
