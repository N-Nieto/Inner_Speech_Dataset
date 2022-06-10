# -*- coding: utf-8 -*-

"""
Created on Wed Oct 16 15:18:45 2019
Last Update: 09/06/2022

@author: Nieto Nicolás
@email: nnieto@sinc.unl.edu.ar
"""

import mne
import numpy as np

def Event_correction(N_S,N_E,events):


    # Exclude this tag from the events
    events=mne.pick_events(events, exclude=65536)

    # Counts the events ===================================================
    # Initialize vars
    Events_code=np.zeros([len(events[:,2]) ,2],dtype=int)
    Events_code[:,0]=events[:,2]

    Events_uniques=np.unique(Events_code[:,0]);

    Event_count=np.zeros([len(Events_uniques),2 ],dtype=int)
    Event_count[:,0]= Events_uniques
        
    # Count 
    a=0
    for i in Events_uniques:
       Event_count[a,1]= len(np.extract(Events_code==Events_uniques[a], Events_code)  )
       a=a+1

# CHECK EVETS =========================================================
#         WORKS ONLY IF ARE NOT 2 CONSECUTIVES TAGS MISSING
# =============================================================================
    Warnings=0
    # Warning missing code
    Warnings_code=[0]
    # Warning positions
    Warnings_pos=[0]
    
    for i in range (len (Events_code)):
        Events_code[i,1] = i

        # Check Tags  code = 31 32 33 34
        # Find the star mark
        if Events_code[i,0] == 42:
            # If the next mark is the tag is OK
            if (Events_code [i+1,0]==31 or Events_code [i+1,0]==32 or Events_code [i+1,0]==33 or Events_code [i+1,0]==34):
                # Do nothing
                pass
            # If the next mark is the mark for concentration the tag is missing
            elif Events_code [i+1,0]==44:
                min_tag= min(Event_count[Event_count[:,0]==31,1],Event_count[Event_count[:,0]==32,1],Event_count[Event_count[:,0]==33,1],Event_count[Event_count[:,0]==34,1])
                miss_tag=Event_count[Event_count[:,1]==min_tag,0]
                print('Warnings, miss '+str(miss_tag)+' at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, miss_tag)
                Warnings_pos=np.append(Warnings_pos,i)

        # Check start and question   code=42,17
        if Events_code[i,0]==46:
            if (Events_code [i+1,0]==42 or Events_code [i+1,0]==16 or Events_code [i+1,0]==17):
                pass
            elif (Events_code [i+1,0]==61 or Events_code[i+1,0]==62 or Events_code[i+1,0]==63 or Events_code[i+1,0]==64):
                print('Warning, miss Question at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, 17)
                Warnings_pos=np.append(Warnings_pos,i)
            else:
                print('Warning, miss start at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, 42)
                Warnings_pos=np.append(Warnings_pos,i)

        if (Events_code [i,0]==21 or Events_code[i,0]==22 or Events_code[i,0]==23):
            if Events_code [i+1,0]==42:
                pass
            else:
                print('Warning, miss start at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, 42)
                Warnings_pos=np.append(Warnings_pos,i)

        
        if (Events_code [i,0]==61 or Events_code[i,0]==62 or Events_code[i,0]==63 or Events_code[i,0]==64):
            if (Events_code [i+1,0]==42 or Events_code [i+1,0]==16)  :
                pass
            else:
                print('Warning, miss start at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, 42)
                Warnings_pos=np.append(Warnings_pos,i)

        # Check  code 44
        if (Events_code [i,0]==31 or Events_code [i,0]==32 or Events_code [i,0]==33 or Events_code [i,0]==34):
            if Events_code [i+1,0]==44:
                pass
            elif Events_code [i+1,0]==45:
                print('Warning, miss Usefull interval at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, 44)
                Warnings_pos=np.append(Warnings_pos,i)


        # Check code 45
        if Events_code[i,0]==44:
            if Events_code [i+1,0]==45:
                pass
            elif Events_code [i+1,0]==46:
                print('Warning, miss Concentration interval at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, 45)
                Warnings_pos=np.append(Warnings_pos,i)

        # Check Code 46
        if Events_code[i,0]==45:
            if Events_code [i+1,0]==46:
                pass
            else:
                print('Warning, miss Rest interval at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, 46)
                Warnings_pos=np.append(Warnings_pos,i)


        # Check Ans Code 65
        if Events_code[i,0]==17:
            if (Events_code [i+1,0]==61 or Events_code[i+1,0]==62 or Events_code[i+1,0]==63 or Events_code[i+1,0]==64):
                pass
            else: 
                print('Warning, miss Answerd at i = '+str(i))
                Warnings=Warnings+1
                Warnings_code= np.append(Warnings_code, 61)
                Warnings_pos=np.append(Warnings_pos,i)
                    
# =============================================================================
# Correcting the events============================


    if Warnings==0:
        print('No Warnings, no corrections of events')
        Events_code_fix= Events_code
        Corrected_events=events
    else:
        print ("Correcting Events")
        # Adding missing values
        Warnings_code=np.delete(Warnings_code,0)
        Warnings_pos=np.delete(Warnings_pos,0)

        corrections=np.zeros([Warnings,3],dtype=int)

        corrections[:,2]=Warnings_code

        for i in range (len(corrections)):
                
               # If a 42 is missing, I was seaching after a 46
               if corrections[i,2]== 42:
                   corrections[i,0]=events[Warnings_pos[i],0]+1945;
                   
               # If a 44 is missing, I was seaching after a 45 
               elif corrections[i,2]== 44:
                   corrections[i,0]=events[Warnings_pos[i],0]+2594;
                   
               #If a 44 is missing, I was seaching after a 46 
               elif corrections[i,2]== 45:
                   corrections[i,0]=events[Warnings_pos[i],0]+1075;
                   
               # If a 46 is missing, I was seaching after a 45 un 46 
               elif corrections[i,2]== 46:
                   corrections[i,0]=events[Warnings_pos[i],0]+1075;
                   
               # If a tag is missing, I was seaching after a 42
               elif corrections[i,2]== 17:
                   corrections[i,0]=events[Warnings_pos[i],0]+2092;
                   
               # If a tag is missing, I was seaching after a 42
               elif corrections[i,2]== 61:
                   corrections[i,0]=events[Warnings_pos[i],0]+2092;
               # If a tag is missing, I was seaching after a 42
               elif corrections[i,2]== miss_tag:
                   corrections[i,0]=events[Warnings_pos[i],0]+563;
                   
                   
        #Append the missing events
        Corrected_events=np.append(events,corrections,axis=0)
        # Sort the events by the time stamp
        Corrected_events = Corrected_events[Corrected_events[:,0].argsort()]


#CHECK CORRECTED EVETS ===============================================
        Warnings=0
        Warnings_code=[0]
        Warnings_pos=[0]

        Events_code_fix=np.zeros([len(Corrected_events[:,2]) ,2],dtype=int)
        Events_code_fix[:,0]=Corrected_events[:,2]


        for i in range (len (Events_code_fix)):
            Events_code_fix[i,1]=i

            # Check Tags    code= 31 32 33 34
            # Find the star mark
            if Events_code_fix[i,0]==42:
                # If the next mark is the tag is OK
                if (Events_code_fix [i+1,0]==31 or Events_code_fix [i+1,0]==32 or Events_code_fix [i+1,0]==33 or Events_code_fix [i+1,0]==34):
                    pass
                # If the next mark is the mark for concentration the tag is missing
                elif Events_code_fix [i+1,0]==44:
                    # WORKS ONLY IF JUST ONE TAG IS MISSING !!!!
                    min_tag= min(Event_count[Event_count[:,0]==31,1],Event_count[Event_count[:,0]==32,1],Event_count[Event_count[:,0]==33,1],Event_count[Event_count[:,0]==34,1])
                    miss_tag=Event_count[Event_count[:,1]==min_tag,0]
                    print('Warnings, miss '+str(miss_tag)+' at i = '+str(i))
                    Warnings=Warnings+1
                    Warnings_code= np.append(Warnings_code, miss_tag)
                    Warnings_pos=np.append(Warnings_pos,i)

            # Check start      code=42
            if Events_code_fix[i,0]==46:
                if (Events_code_fix [i+1,0]==42 or Events_code_fix [i+1,0]==16 or Events_code_fix [i+1,0]==17):
                    pass
                else:
                    print('Warning, miss start at i = '+str(i))
                    Warnings=Warnings+1
                    Warnings_code= np.append(Warnings_code, 42)
                    Warnings_pos=np.append(Warnings_pos,i)

            if (Events_code_fix [i,0]==21 or Events_code_fix[i,0]==22 or Events_code_fix[i,0]==23):
                if Events_code_fix [i+1,0]==42:
                    pass
                else:
                    print('Warning, miss start at i = '+str(i))
                    Warnings=Warnings+1
                    Warnings_code= np.append(Warnings_code, 42)
                    Warnings_pos=np.append(Warnings_pos,i)

            
            if (Events_code_fix [i,0]==61 or Events_code_fix[i,0]==62 or Events_code_fix[i,0]==63 or Events_code_fix[i,0]==64):
                if (Events_code_fix [i+1,0]==42 or Events_code_fix [i+1,0]==16):
                    pass
                else:
                    print('Warning, miss start at i = '+str(i))
                    Warnings=Warnings+1
                    Warnings_code= np.append(Warnings_code, 42)
                    Warnings_pos=np.append(Warnings_pos,i)

            # Check usefull code 44
            if (Events_code_fix [i,0]==31 or Events_code_fix [i,0]==32 or Events_code_fix [i,0]==33 or Events_code_fix [i,0]==34):
                if Events_code_fix [i+1,0]==44:
                    pass
                elif Events_code_fix [i+1,0]==45:
                    print('Warning, miss Usefull interval at i = '+str(i))
                    Warnings=Warnings+1
                    Warnings_code= np.append(Warnings_code, 44)
                    Warnings_pos=np.append(Warnings_pos,i)


            # Check Usefull code 45
            if Events_code_fix[i,0]==44:
                if Events_code_fix [i+1,0]==45:
                    pass
                elif Events_code_fix [i+1,0]==46:
                    print('Warning, miss Concentration interval at i = '+str(i))
                    Warnings=Warnings+1
                    Warnings_code= np.append(Warnings_code, 45)
                    Warnings_pos=np.append(Warnings_pos,i)

            # Code 46
            if Events_code_fix[i,0]==45:
                if Events_code_fix [i+1,0]==46:
                    pass
                else:
                    print('Warning, miss Rest interval at i = '+str(i))
                    Warnings=Warnings+1
                    Warnings_code= np.append(Warnings_code, 46)
                    Warnings_pos=np.append(Warnings_pos,i)
                   
            # Code 17
            if Events_code_fix[i,0]==17:
                if (Events_code_fix [i+1,0]==61 or Events_code_fix[i+1,0]==62 or Events_code_fix[i+1,0]==63 or Events_code_fix[i+1,0]==64):
                    pass
                else :
                    print('Warning, miss Answerd at i = '+str(i))
                    Warnings=Warnings+1
                    Warnings_code= np.append(Warnings_code, 61)
                    Warnings_pos=np.append(Warnings_pos,i)
                    
                    
        # correcting the events
        if Warnings==0:
            print('Taggs OK')

# CHECK FIXED EVENTS

    # Initialize vars
    Events_uniques_fix=np.unique(Events_code_fix[:,0]);

    Event_count_fix=np.zeros([len(Events_uniques_fix),2 ],dtype=int)
    Event_count_fix[:,0]= Events_uniques_fix

    # Count the events
    a=0
    for i in Events_uniques_fix:
       Event_count_fix[a,1]= len(np.extract(Events_code_fix[:,0]==Events_uniques_fix[a], Events_code_fix[:,0])  )
       a=a+1


# SANITY CHECK AFTER FIX EVETS ===============================================

    # Check if the Begining, End, Baseline start and end are OK
    if (Event_count_fix[Event_count_fix[:,0]==11,1]==1 and Event_count_fix[Event_count_fix[:,0]==12,1]==1 and Event_count_fix[Event_count_fix[:,0]==13,1]==1 and Event_count_fix[Event_count_fix[:,0]==14,1]==1):
        print('Start OK')
    else:
        raise Exception("Missing Stars")

    # Check if blocks are OK
    if Event_count_fix[Event_count_fix[:,0]==15,1] == Event_count_fix[Event_count_fix[:,0]==16,1] == Event_count_fix[Event_count_fix[:,0]==51,1]+1 :
        print('Blocks OK')
    else:
        raise Exception("Missing Blocks")

    # Check if Tags OK
    if Event_count_fix[Event_count_fix[:,0]==31,1] == Event_count_fix[Event_count_fix[:,0]==32,1] == Event_count_fix[Event_count_fix[:,0]==33,1] == Event_count_fix[Event_count_fix[:,0]==34,1]:
        print('Tags OK')
    else:
        raise Exception("Missing Tags")
        
    # Check if Marks OK
    if Event_count_fix[Event_count_fix[:,0]==42,1] == Event_count_fix[Event_count_fix[:,0]==44,1] == Event_count_fix[Event_count_fix[:,0]==45,1] == Event_count_fix[Event_count_fix[:,0]==46,1]:
        print('Marks OK')
    else:
        raise Exception("Missing Marks")

    # Check if Questions OK
    if len (Event_count_fix[Event_count_fix[:,0]==61,1])==0:
        Q_61 = 0    
    else  :  
        Q_61 = Event_count_fix[Event_count_fix[:,0]==61,1][0] 

    if len (Event_count_fix[Event_count_fix[:,0]==62,1])==0:
        Q_62 = 0    
    else  :  
        Q_62 = Event_count_fix[Event_count_fix[:,0]==62,1][0] 

    if len (Event_count_fix[Event_count_fix[:,0]==63,1])==0:
        Q_63 = 0    
    else  :  
        Q_63 = Event_count_fix[Event_count_fix[:,0]==63,1][0] 

    if len (Event_count_fix[Event_count_fix[:,0]==64,1])==0:
        Q_64 = 0    
    else  :  
        Q_64 = Event_count_fix[Event_count_fix[:,0]==64,1][0]
    
    
    if Event_count_fix[Event_count_fix[:,0]==17,1][0] == (Q_61+Q_62+Q_63+Q_64 ):
        print('Cognitive control OK')
    else:
        raise Exception("Missing Congnitive Control Question/Answer")

    return Corrected_events

# =============================================================================
# =============================================================================
    
# In[]
def Cognitive_control_check(events):
    # Check Answers
    Ans_R=0;
    Ans_W=0;
    
    Events_uniques=np.unique(events[:,2])
    Event_count=np.zeros([len(Events_uniques),2 ],dtype=int)
    Event_count[:,0]= Events_uniques
    # Count the events
    a=0
    for i in Events_uniques:
       Event_count[a,1]= len(np.extract(events[:,2]==Events_uniques[a], events[:,2])  )
       a=a+1

    
    for i in range(len(events)):
       if  events[i,2]==17:
           if events[i+1,2]==events[i-4,2]+30:
               Ans_R=Ans_R+1
           else:
               Ans_W=Ans_W+1
               
         
    if Event_count[Event_count[:,0]==17,1] == Ans_R+Ans_W:           
        if Event_count[Event_count[:,0]==17,1] == Ans_R:
            print('All Answers are OK')
        else:
            print('Warning, '+str(Ans_W)+' of ' + str(Event_count[Event_count[:,0]==17,1]) + ' Answers are wrong')
    else:
        raise Exception("Missing Congnitive Control Question/Answer")

    
    return Ans_R , Ans_W 


# =============================================================================
# =============================================================================
# In[]
def Count_events_by_condition(events):
    
    Pron=0
    Im=0
    Vis=0
    
    Pron_count = [0,0,0,0]
    Im_count = [0,0,0,0]
    Vis_count = [0,0,0,0]
    
    for i in range(len(events)):
        
       if  events[i,2]==21:
           Pron=1
           Im=0
           Vis=0
          
           
       if  events[i,2]==22:
           Pron=0
           Im=1
           Vis=0
        
           
       if  events[i,2]==23:
           Pron=0
           Im=0
           Vis=1
          
           
       ## 
       if  events[i,2]==31 :
           if Pron==1:
               Pron_count[0]=Pron_count[0]+1
           elif Im==1:
               Im_count[0]=Im_count[0]+1
               
           elif Vis==1:
               Vis_count[0]=Vis_count[0]+1
       ###        
       elif events[i,2]==32:
           if Pron==1:
               Pron_count[1]=Pron_count[1]+1
           elif Im==1:
               Im_count[1]=Im_count[1]+1
               
           elif Vis==1:
               Vis_count[1]=Vis_count[1]+1
               
       ####        
       elif events[i,2]==33:
           if Pron==1:
               Pron_count[2]=Pron_count[2]+1
           elif Im==1:
               Im_count[2]=Im_count[2]+1
               
           elif Vis==1:
               Vis_count[2]=Vis_count[2]+1
               
       ###        
       elif events[i,2]==34:
           if Pron==1:
               Pron_count[3]=Pron_count[3]+1
           elif Im==1:
               Im_count[3]=Im_count[3]+1
               
           elif Vis==1:
               Vis_count[3]=Vis_count[3]+1
               
    if (min(Pron_count)==max(Pron_count) and min(Im_count)==max(Im_count) and min(Vis_count)==max(Vis_count)):
        print("Tags are ok")
    else:
       raise Exception("Missing or incorrect tags")

    return Pron_count , Im_count , Vis_count
           
# In[]
def Add_block_tag(events, N_B):
    # Create the tag Vector
    Stage_tag=N_B*np.ones(events.shape[0],dtype=int)
    # Stack with the event matrix
    events_taged= np.hstack((events,Stage_tag[:,None]))

    return events_taged


# In[]
def Add_condition_tag(events):

    # Create the tag Vector
    Mod_tag=0
    Mod=0
    for i in range(len(events)):
        
       if  events[i,2]==21:
           Mod=0

       if  events[i,2]==22:
           Mod=1

       if  events[i,2]==23:
           Mod=2

       Mod_tag = np.append(Mod_tag,Mod)
    
    Mod_tag= np.delete(Mod_tag,0)
    # Stack with the event matrix
    events_taged= np.hstack((events,Mod_tag[:,None]))

    events_taged=mne.pick_events(events_taged, include=[31,32,33,34])
    
    return events_taged

# In[]
def Delete_trigger(events):
    
    events=np.delete(events,1,axis =1)
    
    return events

 # In[]   
def Standarized_labels(events):
    # Change the labels 
    # 31 -> 0   "Arriba"    / "Up"
    # 32 -> 1   "Abajo"     / "Down"
    # 33 -> 2   "Derecha"   / "Rigth"
    # 34 -> 3   "Izquierda" / "Left"
    events[:,1]=events[:,1]-31
    
    return events

# In[]
def Check_Baseline_tags(events):
    # The "raw" events should star as [65536,11,13,14,15....]
    # The event 65536 is deleted later in the Events_Correction
    
    
    
    # The tag 14 (end of baseline) should be in the 4 row in the 3 column 
    if events[3,2]!=14:
        #Add Baseline event
        # The baseline duration is 15 seconds, (sf=1024)
        # Add the event 15 seconds after the start Baseline cue
        time = events[2,0]+15*1024
        correction=[time,0,14]
        events= np.vstack([events,correction])
        events = events[events[:,0].argsort()]
        
    return events
    
