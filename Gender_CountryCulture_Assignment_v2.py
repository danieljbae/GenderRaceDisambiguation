# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 22:09:05 2020

@author: danie
"""

import pandas  as pd
import re
import numpy as np
import time

# Hash table for IBM consistnent culture scope
import IBM_culture_map
culture_dict = IBM_culture_map.culture_dict

# Hash table for WGND and IBM consistnent country format 
import WGND_countrycode_map
CC = WGND_countrycode_map.CC # Hash table to map country codes -> Country names
res = WGND_countrycode_map.res # Reverse of @CC to map Country names -> country codes 

# Data Frame for WGND Data
import WGND_lookuptable
wgnd_map = WGND_lookuptable.wgnd_map


def file_reader(file_name, person_type): 
    """ Creating Dataframes for:
    First names + Last name analysis to assign gender and country/culture respectively

    @param(str) file_name: Output from IBM GNR 
    @param(str) assign_type: flag to format tables differently per examiner and lawyer
    @returns(DataFrame) clean_df_master,clean_df_gender,clean_df_country: dataframes of all names for gender and country assignment
    @returns(DataFrame) clean_df_country: dataframe to assign country to every ID using data from IBM.
    """
    # Gender and Country/Culture Dataframes for Examiners
    if person_type == "Examiners":
        
        clean_df_master = pd.read_csv(file_name)
        
        #### IBM Dataframe: Gender ####   
        clean_df_gender = clean_df_master.copy()
        clean_df_gender = clean_df_gender.fillna("")
        clean_df_gender.insert(9, 'Female Classification', "TBD")
        clean_df_gender.insert(10, 'Male Classification', "TBD")
        
        #### IBM Dataframe: Country/Culture ####   
        clean_df_country = clean_df_master[['ExaminerID', 'FirstName', 'LastName', 'Country 1','Top Culture','Unnamed: 31',
                                       'Unnamed: 32', 'Unnamed: 33', 'Unnamed: 34', 'Unnamed: 35', 'Unnamed: 36',
                                        'Unnamed: 37','Unnamed: 38', 'Unnamed: 39']].copy()
        clean_df_country = clean_df_country.fillna("")
        clean_df_country = clean_df_country.rename(columns={"Unnamed: 31": "Top Culture 2"  # Rename Culture Columns
                                         ,"Unnamed: 32": "Top Culture 3"
                                         ,"Unnamed: 33": "Top Culture 4"
                                         ,"Unnamed: 34": "Top Culture 5"
                                         ,"Unnamed: 35": "Top Culture 6"
                                         ,"Unnamed: 36": "Top Culture 7"
                                         ,"Unnamed: 37": "Top Culture 8"
                                         ,"Unnamed: 38": "Top Culture 9"
                                         ,"Unnamed: 39": "Top Culture 10"})
        
        return clean_df_master,clean_df_gender,clean_df_country
    
    # Gender and Country/Culture Dataframes for Lawyers
    elif person_type == "Lawyers":
        
        #### IBM Dataframe: Gender #### 
        clean_df_master = pd.read_csv(file_name)
        clean_df_gender = clean_df_master
        clean_df_gender = clean_df_gender.fillna("")
        clean_df_gender.insert(9, 'Female Classification', "TBD")
        clean_df_gender.insert(10, 'Male Classification', "TBD")
        
        #### IBM Dataframe: Country/Culture #### 
        clean_df_country = clean_df_master.copy()
        clean_df_country = clean_df_country.fillna("")
        
        return clean_df_master,clean_df_gender,clean_df_country
             


def IBM_GenderCutoff(clean_df_gender,threshold): # O(n)
    """ Create Column with Genders assignment value of 1 or 0 
        Based off defined thresholds (95%)

     @param clean_df_gender (data frame): dataframe for IBM output file
     @param threshold(int): chosen threshold for assigning Genders (ex. 95)
     @return (dataframe,dataframe) clean_df_gender: dataframe with Row Level Gender Assignment 
     """
    
    # Threshold Assignment for Females and Males can be seperated for flexibility 
    
    ### Assigning Females to every row ###
    female_threshold = threshold
    female_percent_df = clean_df_gender['Female %'] # Female Confidence Score from IBM for each name
    female_classification = [] # List for female gender assignments
    for val in female_percent_df: 
        try:
             # IBM value for first name was greater than threshold
             if val >= female_threshold:
                 female_classification.append(1)
             else:
                 female_classification.append(0)
        
        # No gender frequency value provided by IBM or first name
        except:
            female_classification.append(0)
   
    
   ### Assigning Males to every row ###
    male_threshold = threshold
    male_percent_df = clean_df_gender[' Male %']
    male_classification = []
    for val in male_percent_df: 
        try:
            # IBM value for first name was greater than threshold
            if val >= male_threshold:
                male_classification.append(1)
            else:
                male_classification.append(0)
                
        # No gender frequency value provided by IBM or first name
        except:
            male_classification.append(0)

    ### Adding Column of Row level Gender Classification
    clean_df_gender['Female Classification'] = female_classification
    clean_df_gender['Male Classification'] = male_classification
    
    # Remove unnecesary columns 
    clean_df_gender = clean_df_gender.loc[:,'ExaminerID':'Male Classification']

    # Create key column for "ID,first" - to perform Assignment of Gender
    clean_df_gender['First_ID_String'] = clean_df_gender['ExaminerID'].apply(str).replace('\.0', '', regex=True)
    clean_df_gender['Key_ID_First'] = clean_df_gender['First_ID_String'] +","+ clean_df_gender['FirstName']

    return clean_df_gender  # Return both as the extra columns are needed for later analysis


def IBM_SuperCulture(clean_df_country): # O(nk), best case is O(n). Where k is the unique number of cultures for a given name
    """ 
    Assigning "Super Culture" to every Row. "Super Culture" is assigned if all cultures on a given row match. Otherwise "Ambigious" is assigned
    
    @param clean_df_country (data frame): dataframe for IBM output file for country analysis
    @return (dataframe,dataframe) clean_df_country: dataframe with Row Level Gender Assignment, same dataframe less columns
    @return (dataframe,dataframe) WGND_row_culture: dataframe for joining first names to "Master" output file
    """
    super_culture = [] # List to contain every row's "super culture"
    
    # Search every Name (zip: remove overhead of dataframe)
    for c1,c2,c3,c4,c5,c6,c7,c8,c9,c10 in zip(clean_df_country['Top Culture'], clean_df_country['Top Culture 2'],clean_df_country['Top Culture 3'],clean_df_country['Top Culture 4'],clean_df_country['Top Culture 5'],clean_df_country['Top Culture 6'],
                                              clean_df_country['Top Culture 7'],clean_df_country['Top Culture 8'],clean_df_country['Top Culture 9'],clean_df_country['Top Culture 10']):
        super_ls = []
        all_10cultures = set((c1,c2,c3,c4,c5,c6,c7,c8,c9,c10))
        flag = False
        
        # Search all cultures for a Name 
        for culture_key in all_10cultures:
            
            # Convert each culture to a broader culture (ex Korean -> Asian)
            if culture_key in culture_dict:
                super_culture_val = culture_dict[culture_key]
                super_ls.append(super_culture_val)
            
            # Skip Name if more than 1 culture found in coversion
            if len(set(super_ls)) > 1:
                super_culture.append("No certain culture")
                flag = True 
                break 
            
        super_set = set(super_ls)
        
        # If more then one culture found in conversion process, skip already marked 
        if flag == True:
            continue
        
        # If no cultures found in IBM
        elif len(super_set) == 0:
            super_culture.append("Ambiguous")
            continue
        
        # If there is only 1 unique culture in a row: we can assign super culture, as such culture
        elif len(super_set) == 1:
            super_culture.append(super_ls[0])
        
        
    # Insert every name's super culture
    clean_df_country.insert(4, 'super_culture', super_culture)

    # Create key column for "ID,last" - to perform Assignment of Country and Culture 
    clean_df_country['P_ID_String'] = clean_df_country['ExaminerID'].apply(str).replace('\.0', '', regex=True)
    clean_df_country['LastName_Key'] = clean_df_country['P_ID_String']+","+clean_df_country['LastName']
    
    # Reduce columns
    row_culture = clean_df_country.loc[:,['ExaminerID','LastName','Country 1','super_culture','LastName_Key']].copy() 
    
    # Saving Data frame to merge with WGND, as we need a pair of name and country to assign Gender in WGND
    WGND_row_culture = clean_df_country.copy()
    WGND_row_culture = WGND_row_culture.loc[:,['ExaminerID','FirstName','LastName','Country 1','super_culture','LastName_Key']]    
    
    return row_culture,WGND_row_culture




def Row_Frequencies(patent_map,col_id_name_key, col_person_id): # O(n)
    """
    Creates a Hash Table that:
    counts unique First/Last name of a occurences in the Patent Data 
    
    @param(dataframe) patent_map: Patent Data to accumulate and apply frequencies
    @param(str) col_id_name_key: column name in @patent_map, which stores keys  ('10007,RODNEY H') 
    @param(str) col_person_id: column name in @patent_map, which store the ID of spelling ("10007") *Join key*
    @return(Hash/Dictionary) idName_freq: where keys are ID,Name and values are [count of spelling, ID]
    ex. of a key, value pair ('10007,RODNEY H') = [4657, '10007']
    """
    
    idName_freq = {}
    keys = list(patent_map[col_id_name_key])
    IDs = list(patent_map[col_person_id]) 
        
    for i in range(len(keys)):
        if keys[i] in idName_freq:
            idName_freq[keys[i]][0] += 1 
        else:
            idName_freq[keys[i]] = [1,IDs[i]] 
    return idName_freq


def merge_two_hashtables(hash_A, hash_B): # O(n)
    """
    Merge values of 2 hash tables by a common key, to create 1 Hash Table
    
    @param(hastable) hash_A: Examiner Primary patent counts
    @param(hastable) hash_B: Examiner Assistant patent counts
    @return(hastable) ID_count: Combined patent counts per common keys
    
    ex. hash_A as Primary: ('10007,RODNEY H')=[4657, '10007']  |  hash_B as Assistant = ('10007,RODNEY H')=[147, '10007']  ===> key,val in Hashtable @ID_Count ('10007,RODNEY H')=[4804, '10007']
    """
    
    ID_count = hash_A.copy()
    for key in hash_B:
        if key in ID_count:
            ID_count[key][0] += hash_B[key][0]
        else:
            ID_count[key] = hash_B[key]
    return ID_count



def patentdata_name_frequency_wrapper(file_name,patent_map,col_id_name_key, col_person_id, *args, **kwargs):
    """
    This function serves 2 purposes: 
    1) counts the occurences of each time a key (id, first or last name) appears in Patent data 
    2) If Examiners - Merges counts for Examiner names that are primary and assistant 
    
    @param(dataframe) patent_map: Patent Data to accumulate and apply frequencies
    @param(str) col_id_name_key: column name in @patent_map, which stores keys  ('10007,RODNEY H') 
    @param(str) col_person_id: column name in @patent_map, which store the ID of spelling ("10007") *Join key*
    @*args, @**kwargs: Addtional/Optional paramters for account for Assistant ID 
    
    Returns (hashtable) @ID_Name_Freq: where keys are ID,Name and values are [count of spelling, ID]
    """

    # Examiners: make 2 hash tables 1 for primary and 1 for assistant name counts in patent data
    if file_name == "ExaminerPatentMap.csv":        
        # 1) Primary ID Examiners: Hash Table for Unique First Names
        Primary_ID_FirstName_Freq = Row_Frequencies(patent_map,col_id_name_key, col_person_id)
        
        # Addtional/Optional paramters for account for Assistant ID 
        assistantID_patent_map = kwargs.get("a", None) # defining optional Params to accomodate this
        assistantID_col_id_name_key = kwargs.get("b", None)
        assistantID_col_person_id = kwargs.get("c", None)
        # Assistant ID Examiners: Hash Table for Unique First Names
        Assistant_ID_FirstName_Freq = Row_Frequencies(assistantID_patent_map,assistantID_col_id_name_key, assistantID_col_person_id)

        # 2) Creating Hash Table to count total times a unique name appears as a Primary or Assistant ID
        examiner_ID_count = merge_two_hashtables(Primary_ID_FirstName_Freq,Assistant_ID_FirstName_Freq)  

        return examiner_ID_count
    
    elif file_name == "LawyerPatentMap.csv":
        # 1) Primary ID Examiners: Hash Table for Unique First Names
        ID_Name_Freq = Row_Frequencies(patent_map,col_id_name_key, col_person_id)       
        return ID_Name_Freq
        

    

def patentdata_map(file_name):
    """ Create Hash Table to store: Name counts in Patent Data 
    
    1) Creating a key in Patent Data (ID, First/Last Name) 
       - If Examiner: 4x possible keys, due to assitant ID
    2) Create Hash Table to store name counts
    
    @param file_name (str): Patent data file ename (Flag for examiner, as primary and assistant counts are merged)
    @return examiner_ID_count, examiner_ID_count_last (Hash Table): where keys are ID,Name and values are [count of spelling, ID]
    """

    
    if file_name == "ExaminerPatentMap.csv":
        Examiner_map = pd.read_csv(file_name)
        Examiner_map = Examiner_map.fillna("")    

        ### Drops specific to Primary Examiners 
        Examiner_Map_Keys = Examiner_map.copy()
        Examiner_Map_Keys_Primary = Examiner_Map_Keys.drop(Examiner_Map_Keys[Examiner_Map_Keys.PrimaryID == ''].index)
        Examiner_Map_Keys_Primary = Examiner_Map_Keys_Primary.drop(Examiner_Map_Keys_Primary[Examiner_Map_Keys_Primary.Primary_Firstname == ''].index)
        Examiner_Map_Keys_Primary = Examiner_Map_Keys_Primary.drop(Examiner_Map_Keys_Primary[Examiner_Map_Keys_Primary.Primary_Lastname == ''].index)
        
        ### Drops specific to Assistant Examiners 
        copy_Examiner_map = Examiner_map.copy()
        copy_Examiner_map = copy_Examiner_map.dropna()
        copy_Examiner_map['AssistantID'].replace('', np.nan, inplace=True) # Patents do not always have an Assistant Examiner present
        copy_Examiner_map.dropna(subset=['AssistantID'], inplace=True) # Patents do not always have an Assistant Examiner present
        Examiner_Map_Keys_Assistant = copy_Examiner_map.drop(copy_Examiner_map[copy_Examiner_map.AssistantID == ''].index)
        Examiner_Map_Keys_Assistant = Examiner_Map_Keys_Assistant.drop(Examiner_Map_Keys_Assistant[Examiner_Map_Keys_Assistant.Assistant_FirstName == ''].index)
        Examiner_Map_Keys_Assistant = Examiner_Map_Keys_Assistant.drop(Examiner_Map_Keys_Assistant[Examiner_Map_Keys_Assistant.Assistant_Lastname == ''].index)

        ####  First Name analysis
        # 1A) Create key (Primary id, first name)
        Examiner_Map_Keys_Primary['P_ID_String'] = Examiner_Map_Keys_Primary['PrimaryID'].apply(str).replace('\.0', '', regex=True)
        Key_PrimaryID = Examiner_Map_Keys_Primary['P_ID_String'] 
        Examiner_Map_Keys_Primary['Key_PID_First'] = Examiner_Map_Keys_Primary['P_ID_String'] +","+ Examiner_Map_Keys_Primary['Primary_Firstname']
        PrimaryFirst_Map = Examiner_Map_Keys_Primary[['Patent','Key_PID_First','Primary_Firstname','PrimaryID','P_ID_String']]
        # 1B) Create key (Assistant id,first name)
        Examiner_Map_Keys_Assistant['A_ID_String'] = Examiner_Map_Keys_Assistant['AssistantID'].apply(str).replace('\.0', '', regex=True)
        Key_AssistantID = Examiner_Map_Keys_Assistant['A_ID_String'] 
        Examiner_Map_Keys_Assistant['Key_AID_First'] = Examiner_Map_Keys_Assistant['A_ID_String'] +","+ Examiner_Map_Keys_Assistant['Assistant_FirstName']
        AssistantFirst_Map = Examiner_Map_Keys_Assistant[['Patent','Key_AID_First','Assistant_FirstName','AssistantID','A_ID_String']]
                
        # 2) Count how many times a given key appears in patent data -- Merge w/ Assisntant results for Examiners only 
        examiner_ID_count = patentdata_name_frequency_wrapper(file_name, PrimaryFirst_Map,'Key_PID_First','P_ID_String', 
                                                     a=AssistantFirst_Map, b='Key_AID_First', c='A_ID_String')
        
        #### Last Name analysis
        Examiner_Map_Keys_Primary_Culture = Examiner_Map_Keys_Primary.copy()
        Examiner_Map_Keys_Primary_Culture_last = Examiner_Map_Keys_Assistant.copy()
        # 1A) Create key (Primary id,:ast name)
        Examiner_Map_Keys_Primary_Culture['P_ID_String'] = Key_PrimaryID
        Examiner_Map_Keys_Primary_Culture['Key_PID_Last'] = Examiner_Map_Keys_Primary_Culture['P_ID_String']+","+Examiner_Map_Keys_Primary_Culture['Primary_Lastname']
        PrimaryLast_Map = Examiner_Map_Keys_Primary_Culture[['Patent','Key_PID_Last','Primary_Lastname','PrimaryID','P_ID_String']].copy()
        # 1B) Create key (Assistant id, Last name)
        Examiner_Map_Keys_Primary_Culture_last['A_ID_String'] = Key_AssistantID
        Examiner_Map_Keys_Primary_Culture_last['Key_AID_Last'] = Examiner_Map_Keys_Primary_Culture_last['A_ID_String']+","+Examiner_Map_Keys_Primary_Culture_last['Assistant_Lastname']
        AssistantLast_Map = Examiner_Map_Keys_Primary_Culture_last[['Patent','Key_AID_Last','Assistant_Lastname','AssistantID','A_ID_String']].copy() 
        
        # 2) Count how many times a given key appears in patent data -- Merge w/ Assisntant results for Examiners only 
        examiner_ID_count_last = patentdata_name_frequency_wrapper(file_name, PrimaryLast_Map,'Key_PID_Last','P_ID_String', 
                                                     a=AssistantLast_Map, b='Key_AID_Last', c='A_ID_String')
        
        return examiner_ID_count, examiner_ID_count_last
                    
    elif file_name == "LawyerPatentMap.csv": 
        Lawyer_map = pd.read_csv(file_name)
        Lawyer_map = Lawyer_map.fillna("")
        Lawyer_map_Keys = Lawyer_map.copy()
        ### Drops for Lawyers 
        Lawyer_map_Keys_clean = Lawyer_map_Keys.drop(Lawyer_map_Keys[Lawyer_map_Keys.NewID == ''].index)
        Lawyer_map_Keys_clean = Lawyer_map_Keys_clean.drop(Lawyer_map_Keys_clean[Lawyer_map_Keys_clean.Firstname == ''].index)
        Lawyer_map_Keys_clean = Lawyer_map_Keys_clean.drop(Lawyer_map_Keys_clean[Lawyer_map_Keys_clean.LastName == ''].index)
        
        
        ####  First Name analysis
        # 1) Create key (id, first name)
        Lawyer_map_Keys_clean['P_ID_String'] = Lawyer_map_Keys_clean['NewID'].apply(str).replace('\.0', '', regex=True)
        Key_PrimaryID = Lawyer_map_Keys_clean['P_ID_String'] 
        Lawyer_map_Keys_clean['Key_PID_First'] = Lawyer_map_Keys_clean['P_ID_String'] +","+ Lawyer_map_Keys_clean['Firstname']
        PrimaryFirst_Map = Lawyer_map_Keys_clean[['Patent','Key_PID_First','Firstname','NewID','P_ID_String']]
        
        # 2) Count how many times a given key appears in patent data 
        examiner_ID_count = patentdata_name_frequency_wrapper(file_name, PrimaryFirst_Map,'Key_PID_First','P_ID_String')
    
    
        #### Last Name analysis
        Lawyer_map_Keys_Primary_Culture = Lawyer_map_Keys_clean.copy()
        # 1) Create key (Primary id,:ast name)
        Lawyer_map_Keys_Primary_Culture['P_ID_String'] = Key_PrimaryID
        Lawyer_map_Keys_Primary_Culture['Key_PID_Last'] = Lawyer_map_Keys_Primary_Culture['P_ID_String']+","+Lawyer_map_Keys_Primary_Culture['LastName']
        PrimaryLast_Map = Lawyer_map_Keys_Primary_Culture[['Patent','Key_PID_Last','LastName','NewID','P_ID_String']].copy()

        # 2) Count how many times a given key appears in patent data -- Merge w/ Assisntant results for Examiners only 
        examiner_ID_count_last = patentdata_name_frequency_wrapper(file_name, PrimaryLast_Map,'Key_PID_Last','P_ID_String')
        
        
        return examiner_ID_count, examiner_ID_count_last 
        

       
def apply_patentfreq(patent_frequencyTable, IBM_table,assign_type): # O(n)
    """
    Joins frequnecies to every row/name to the data frame containing IBM data 
    
    @param(hash table) patent_frequencyTable: contains the count of a given "id,name" in patent data
    @param(data frame) IBM_table: table for every lawyer/examiner name with IBM gander or country data 
    @return(data frame) IBM_table_updated: every row of @IBM_table will now how extra columns on it 
    """
    
    if assign_type == "gender":       
        # Storing IBM values to create Hash table 
        gender_IBM_keys = list(IBM_table['Key_ID_First'])
        femalescore_IBM = list(IBM_table['Female %'])
        malescore_IBM = list(IBM_table[' Male %'])
        
        # Create hash table from IBM data, example entry in hash: classifications['10007,RODNEY H']=[0.0 female, 98.0 male]
        classifications = {} 
        for key in range(len(gender_IBM_keys)):
            if gender_IBM_keys[key] in classifications:
                continue
            else: # Intialize Female % and Male %
                classifications[gender_IBM_keys[key]] = [femalescore_IBM[key],malescore_IBM[key]] # [Female %, Male %]
        
        # joining hash tables by appending freq info to hashtable
        for key in patent_frequencyTable:
            if key in classifications:
                patent_frequencyTable[key].append(classifications[key][0]) # Count
                patent_frequencyTable[key].append(classifications[key][1]) # ID 
        
        return patent_frequencyTable # example entry in merged hash: ('10007,RODNEY H')=[4804, '10007', 0.0, 98.0]

    elif assign_type == "country":
        # Storing IBM values to create Hash table 
        lastname_classifications_keys = list(IBM_table['LastName_Key'])
        country_classifications_val = list(IBM_table['Country 1'])
        culture_classifications_val = list(IBM_table['super_culture'])
        
        # Create hash table from IBM data, example entry in hash: classifications['10007,BONCK']=['Belgium', 'Anglo']
        classifications_last = {}
        for key in range(len(lastname_classifications_keys)):
            if lastname_classifications_keys[key] in classifications_last:
                continue
            else: # Intialize Country and Culture
                classifications_last[lastname_classifications_keys[key]] = [country_classifications_val[key],culture_classifications_val[key]] # [Country, "Super Culture"]
       
        # joining hash tables by appending freq info to hashtable  
        for key in patent_frequencyTable:
            if key in classifications_last:
                patent_frequencyTable[key].append(classifications_last[key][0]) # Count
                patent_frequencyTable[key].append(classifications_last[key][1]) # ID
                
        return patent_frequencyTable # example entry in merged hash: ('10007,BONCK'): [4816, '10007', 'Belgium', 'Anglo']
        
        
          
def ls_met_threshold(top_ID_count,name_frequencies,freq_threshold,assign_type):
    """ Returns a list of names that meet assignement conditions
    
    @param (hash table) top_ID_count: where keys are ID,Name and values are [count of spelling, ID] 
    @param(list) name_frequencies: patent name % values
    @param (float) freq_threshold: patent % threshold for first or last name
    @param(str) assign_type: determines assignment conditions
    @return(list) met_threshold: a list of values that meet assignment conditions for Gender and Country/Culture
    """
    count,total,cursor,met_threshold = 0,0,0,[]
      
    for key in top_ID_count:
        try:
            if (assign_type == "gender" and (top_ID_count[key][3]>= 95 or top_ID_count[key][4] >= 95) and (name_frequencies[cursor] >= freq_threshold) ):
                count += 1
                met_threshold.append(top_ID_count[key][0])
            elif (assign_type == "country" and top_ID_count[key][3] != "") and (name_frequencies[cursor] >= freq_threshold):  
                    count += 1
                    met_threshold.append(top_ID_count[key][0])
            total += 1     
        except:
            total += 1
        cursor += 1
    return met_threshold


def convert_todataframe(top_ID_count,assign_type,freq_threshold):
    """ This function serves 2 purposes: 
    1) Converts - top selected name hash table, into a data frame
    2) Assigns - based off patent frequency threshold 
    
    @param (hash table) top_ID_count: where keys are ID,Name and values are [count of spelling, ID] 
    @param (str) assign_type:  determines assignment conditions
    @param (float) freq_threshold: patent % threshold for first or last name
    @return (dataframes) final_df,classified,not_classified: dataframes for names that have gender and cultures, assigned or not 
    """
    
    
    #### Convert Hash Table into Data Frame ####
    df2 = pd.DataFrame(top_ID_count.items(), columns=['Examiner_ID','Classifications']) 
    
    if assign_type == "gender":
        df2[['Key_Top_Spelling','Freq','Total','Female%','Male%']] = pd.DataFrame(df2.Classifications.tolist())
        final_df = pd.DataFrame(df2['Classifications'].to_list(), columns=['Key_Top_Spelling','Freq','Total','Female%','Male%'],index= df2.index)
        final_df.insert(loc=0, column='Examiner_ID', value=df2['Examiner_ID']) 
        final_df.insert(loc=4, column='Freq%', value=round(final_df['Freq']/final_df['Total'],2)) #Calculating top name's count proportion
        keycol_name = "Key_Top_Spelling"
    
    elif assign_type == "country":
        df2[['Key_Top_Spelling_LastName','Freq','Total','TopCountry','SuperCulture']] = pd.DataFrame(df2.Classifications.tolist())
        final_df = pd.DataFrame(df2['Classifications'].to_list(), columns=['Key_Top_Spelling_LastName','Freq','Total','TopCountry','SuperCulture'],index= df2.index)
        final_df.insert(loc=0, column='Examiner_ID', value=df2['Examiner_ID']) 
        final_df.insert(loc=4, column='Freq%', value=round(final_df['Freq']/final_df['Total'],2)) #Calculating top name's count proportion
        keycol_name = "Key_Top_Spelling_LastName"

    #### Apply Threshold #####
    name_frequencies = list(final_df['Freq%'])
    # Returns a list of which examiners or lawyers have met our thresholds to assign their gender
    met_threshold = ls_met_threshold(top_ID_count,name_frequencies,freq_threshold,assign_type)
    
    classified = final_df[final_df[keycol_name].isin(met_threshold)].copy()
    not_classified = final_df[~final_df[keycol_name].isin(met_threshold)].copy()
    
    # Create column for just the first and last name 
    classified['spelling'] =  [x.split(",")[1] for x in classified[keycol_name]]
    not_classified['spelling'] =  [x.split(",")[1] for x in not_classified[keycol_name]]


    return final_df,classified,not_classified





def collapse_id(hash_preName_selection,assign_type,freq_threshold):
    """
    Selects the a name spelling within an ID. A name is selected amongst other names if it is the most frequent or has non-ambigious values
    The  commented term "classification" refers to the the @hash_preName_selection values, formatted as - [Name Spelling, Patent count, Cumulative count for ID, IBM Female %,IBM Male %]
    
    @param(hash table) hash_preName_selection: where keys are ID,Name and values are [count of spelling, ID,ibm data,ibm data]
    @param (str) assign_type:  determines assignment conditions
    @param (float) freq_threshold: patent % threshold for first or last name
    
    @return(hash table)top_ID_count: where where keys are ID,Name and values are [count of spelling, ID, ibm data, ibm data]
    ex. top_ID_count['10007'] = ['10007,RODNEY H', 4804, 4843, 0.0, 98.0]
    Note: 0 is a valid gender score, below 0 indicates ambigious
    """

    ############# Collpase logic for Genders ############# 
    if assign_type == "gender":
        # counter = 0 # Edge Cases
        # Hash Table to store 1 selected name for every ID
        top_ID_count = {}
        # Search all unique first names relative to ID  (first_id_key - ex. '10007,RODNEY H')
        for first_id_key in hash_preName_selection: #O(n) where n is ~43k all unique first names (from set of 52k names)
            examiner_id = hash_preName_selection[first_id_key][1]
            
            ### Compare spellings within ID
            if examiner_id in top_ID_count:
                
                try: # Try checks if: Spelling in Directory or GNR Analysis (ex. +1 word), if so we have "classification" data
                    update_vals = [None]*5
                    update_vals[0],update_vals [1],update_vals [2],update_vals [3],update_vals [4] = first_id_key,hash_preName_selection[first_id_key][0],top_ID_count[examiner_id][2] + hash_preName_selection[first_id_key][0],hash_preName_selection[first_id_key][2],hash_preName_selection[first_id_key][3]
                    
                    # If Current gender scores are "Ambigious"
                    if top_ID_count[examiner_id][3] < 0 or top_ID_count[examiner_id][4] < 0:
                        ## If new spelling is more frequent
                        if (hash_preName_selection[first_id_key][0] > top_ID_count[examiner_id][1]) and (hash_preName_selection[first_id_key][2] >= 0 or hash_preName_selection[first_id_key][3] >= 0):
                            top_ID_count[examiner_id] = update_vals
                        ## Else If new spelling, non-"Ambigious"
                        elif (hash_preName_selection[first_id_key][2] >= 0 or hash_preName_selection[first_id_key][3] >= 0):
                            top_ID_count[examiner_id] = update_vals
                    
                    # Current gender scores are not "Ambigious"
                    else:
                        # If new spelling is more frequent (even if new is "Ambigious")
                        if (hash_preName_selection[first_id_key][0] > top_ID_count[examiner_id][2]):
                            top_ID_count[examiner_id] = update_vals
                        else: # Less than existing: add to Cumulative count
                            top_ID_count[examiner_id][2] += hash_preName_selection[first_id_key][0]
                
                except: # Edge Cases - Spelling not in Directory or GNR Analysis (ex. +1 word), so no "classification" data 
                    continue
                    
            ###  Initialize first value of top name hash table ### 
            else: 
                try: # If Spelling has classification data from IBM (~43k, unique first names)
                    intial_vals = [None]*5
                    intial_vals[0],intial_vals[1],intial_vals[2],intial_vals[3],intial_vals[4] = first_id_key,hash_preName_selection[first_id_key][0],hash_preName_selection[first_id_key][0],hash_preName_selection[first_id_key][2],hash_preName_selection[first_id_key][3]
                    top_ID_count[examiner_id] = intial_vals
                    # '10007,RODNEY H', 4804, //Intial value to accumulate - 4804, Female %, Male %  
                    
                except: # Edge Cases - Spelling not in Directory or GNR Analysis (ex. +1 word), so no classification data
                    continue
        # Convert top name hash table into data frame and classify based off patent frequency threshold   
        final_df,classified,not_classified = convert_todataframe(top_ID_count,assign_type,freq_threshold)
        return final_df,classified,not_classified,top_ID_count
    
    
    ############# Collpase logic for Countries ############# 
    elif assign_type== "country":
        # counter = 0 # Edge Cases

        # Hash Table to store 1 selected name for every ID
        top_ID_count_last = {}
        
        # Search all unique first names relative to ID  (last_id_key - ex. '10007,BONCK')
        for last_id_key in hash_preName_selection:
            examiner_id_last = hash_preName_selection[last_id_key][1]
            
            ### Compare spellings within ID ###
            if examiner_id_last in top_ID_count_last:
                
                try: # Try checks if: Spelling in Directory or GNR Analysis (ex. +1 word), if so we have "classification" data
                    update_vals = [None]*5
                    update_vals[0],update_vals [1],update_vals [2],update_vals [3],update_vals [4] = last_id_key,hash_preName_selection[last_id_key][0],top_ID_count_last[examiner_id_last][2] + hash_preName_selection[last_id_key][0],hash_preName_selection[last_id_key][2],hash_preName_selection[last_id_key][3]
                    
                    # Current Country and Culture "Ambigious"                      
                    if top_ID_count_last[examiner_id_last][2] == "" or top_ID_count_last[examiner_id_last][3] == "Ambiguous":
                        ## If new spelling is more frequent  
                        if (hash_preName_selection[last_id_key][0] > top_ID_count_last[examiner_id_last][1]) and (hash_preName_selection[last_id_key][2] != "" and hash_preName_selection[last_id_key][3] != "Ambiguous"):
                            top_ID_count_last[examiner_id_last] = update_vals
                        ## Else If new spelling, non-"Ambigious"               
                        elif (hash_preName_selection[last_id_key][2]  != "" and  hash_preName_selection[last_id_key][3] != "Ambiguous"):
                            top_ID_count_last[examiner_id_last] = update_vals
                    
                    # Current country or culture, are not "Ambigious"
                    else:
                        ## If new spelling is, more frequent (even if new spelling is "Ambigious")
                        if (hash_preName_selection[last_id_key][0] > top_ID_count_last[examiner_id_last][2]) and (hash_preName_selection[last_id_key][2] != "" and hash_preName_selection[last_id_key][3] != "Ambiguous"):
                            top_ID_count_last[examiner_id_last] = update_vals
                        else: # Less than existing: add to Cumulative count
                             top_ID_count_last[examiner_id_last][2] += hash_preName_selection[last_id_key][0]

                except: # Edge Cases: Spelling not in Directory or GNR Analysis (ex. +1 word), so no "classification" data
                    continue
            
            ###  Initialize first value of top name hash table ### 
            else:
                try: # If Spelling has classification data from IBM (~29k, unique last names)
                    intial_vals = [None]*5
                    intial_vals[0],intial_vals[1],intial_vals[2],intial_vals[3],intial_vals[4] = last_id_key,hash_preName_selection[last_id_key][0],hash_preName_selection[last_id_key][0],hash_preName_selection[last_id_key][2],hash_preName_selection[last_id_key][3]
                    top_ID_count_last[examiner_id_last] = intial_vals
                    # '10007,BONCK', 4816, //Intial value to accumulate - 4816, Belgium, Anglo  

                except: # Edge Cases: Spelling not in Directory or GNR Analysis (ex. +1 word), so no "classification" data
                    continue    
        # Convert top name hash table into data frame and classify based off patent frequency threshold
        final_df,classified,not_classified = convert_todataframe(top_ID_count_last,assign_type,freq_threshold)
        return final_df,classified,not_classified,top_ID_count_last
     
    
def ibm_classified(classified,classified_last,not_classified):
    """ This function parses the data into 2 sets:
    A) Full Assignment: names that have both Gender and Country data assigned  
    B) WGND Data: names that have just Country data assigned, but no gender data 

    @param (dataframe) classified: names where genders have been assigned
    @param (dataframe) classified_last:  names where countries have been assigned
    @param (dataframe) not_classified:  names genders have not been assigned
    @return (dataframes) gender_country_classifiedDf: gender and country have been assigned
    @return (dataframes) not_classified_IDs_genders_country_merge: names where genders has not been assigned 
    """
    # Examiners with country data 
    classified_IDs_genders_full = set(classified_last['Examiner_ID'])
    # Examiners with gender data, that are found in list of exainers with country data
    classified_IDs_genders_country_full = classified[classified['Examiner_ID'].isin(classified_IDs_genders_full)].copy()
    
    # Adding country 
    classified_IDs_genders_country_add = set(classified_IDs_genders_country_full['Examiner_ID'])
    classified_IDs_genders_country_merge = pd.merge(classified_IDs_genders_country_full, classified_last, left_on='Examiner_ID',right_on='Examiner_ID',how='left')

    ### Fully Classified Names (Yes Gender + Yes Country)
    gender_country_classifiedDf = classified_IDs_genders_country_merge.loc[:,['Examiner_ID','Key_Top_Spelling','Female%','Male%','Key_Top_Spelling_LastName','TopCountry','SuperCulture']].copy()

    ### WGND: Names ( No Gender + Yes Country)
    not_classified_IDs_genders = set(classified_last['Examiner_ID']) ## Genders that have not been classified 
    not_classified_IDs_genders_country = not_classified[not_classified['Examiner_ID'].isin(not_classified_IDs_genders)].copy()
    not_classified_IDs_genders_country_add = set(not_classified_IDs_genders_country['Examiner_ID'])
    not_classified_IDs_genders_country_merge = pd.merge(not_classified_IDs_genders_country, classified_last, left_on='Examiner_ID',right_on='Examiner_ID',how='left').copy()
    return gender_country_classifiedDf,not_classified_IDs_genders_country_merge 


    
    
def WGND_assignGender(WGND_df):
    """
    Assign Gender to Names using WGND, based off country
    
    @param (dataframe) WGND_df: names that have just Country data assigned, but no gender data 
    @return (dataframe) df_post_WNGD: names with genders assigned, to names found in WGND
    """
    WGND_df['spelling'] =  [x.split(",")[1] for x in WGND_df['Key_Top_Spelling']] # First Name

    # Converts Pre-WGND to have Country Codes
    codes = []
    no_code = []
    allcountries = list(WGND_df['TopCountry'])
    wgnd_rows = len(allcountries)
    
    for country in range(wgnd_rows):
        if allcountries[country].upper() in res:
            codes.append(res[allcountries[country].upper()])
        else:
            codes.append("No Country WGND Code")
            no_code.append(allcountries[country])
            
    # Add Converted Country Codes, to Pre-WGND df 
    WGND_df['country_code'] = codes
    WGND_df['Name_Country_Key'] = WGND_df['spelling']+ "," + WGND_df['country_code']     
    
    # Creating Key (name,country code) for WGND Gender Look up Table 
    pre_wgnd_names = list(WGND_df['spelling'])
    just_first_names = pre_wgnd_names
    
    for i in range(len(pre_wgnd_names)):
        all_names = []
        person = pre_wgnd_names[i]
        try:
            all_names = person.split()
            just_first_names[i] = all_names[0]
        except:
            just_first_names[i] = person
    
    WGND_df['Just_First_Name'] = just_first_names
    WGND_df['First_Name_Country_Key'] = WGND_df['Just_First_Name']+ "," + WGND_df['country_code'] 

    ### Use WGND Lookup Table to assign Genders
    # Join Examiners with countries to WGND
    wgnd_First_merge = pd.merge(WGND_df, wgnd_map, left_on='Name_Country_Key',right_on='First_Name_Country_Key',how='left') # Full name ex. "Daniel J" --- Not used
    wgnd_justFirst_merge = pd.merge(WGND_df, wgnd_map, left_on='First_Name_Country_Key',right_on='First_Name_Country_Key',how='left') # Just first ex. "Daniel" --- Join based off this
    
    # Filter data: Remove any rows where WGND lookup table did not find a country for a given name,country pair
    post_WNGD_first = wgnd_First_merge.dropna()  # Not used
    post_WNGD_JustFirst = wgnd_justFirst_merge.dropna() # Join based off this
    
    # Filter data: Retain only those where WGND returned Male or Female. 
    # Because WGND lookup table can contain a given name,country --- but cannot determine gender (denoted by "?")
    df_post_WNGD = post_WNGD_JustFirst.loc[(post_WNGD_JustFirst['gender']== "M") | (post_WNGD_JustFirst['gender']== "F")]
    df_post_WNGD = df_post_WNGD.rename(columns={"spelling_x": "FirstName"  # Rename Culture Columns
                                         ,"spelling_y": "LastName"
                                         ,"Freq_x":"FirstName%"
                                         ,"Freq_y":"LastName%"
                                         ,"Female%":"IBM Female %"
                                         ,"Male%":"IBM Male %"
                                         ,"TopCountry": "IBM Top Country"
                                         ,"SuperCulture":"IBM_Culture"})
    
    return df_post_WNGD
    
    
    
    
    
def export_files(gender_country_classifiedDf,top_ID_count,not_classified,df_post_WNGD,
                 top_ID_count_last,WGND_row_culture,clean_df_gender,wgnd_map,
                 filename_FullMatches, filename_Master):
    """
    Formatting and Filtering output tables

    @param(dataframe) gender_country_classifiedDf: df that has names with gender and country assigned
    @param(hash table) top_ID_count: table that stores top selected first name
    @param(dataframe) not_classified: df that has names with country assigned, but gender is not assigned
    @param(dataframe) df_post_WNGD: df with WGND gender assignement 
    @param(hash table) top_ID_count_last: table that stores top selected last name
    @param(dataframe) WGND_row_culture: df where all names have a "Super culture" value
    @param(dataframe) clean_df_gender: df where all names have a gender value, based on threhold
    @param(dataframe) wgnd_map: WGND lookup table
    @param(str) filename_FullMatches: full matches file name
    @param(str) filename_Master: master file name
    
    @return (dataframe) all_matches: Assigned Rows, where gender and country have been assigned
    @return (dataframe) Master_file_export: All rows with all data found associated to name
    """
    ##########################################################################################
    # #                       Full Match Files: Post-WGND
    ##########################################################################################
    post_WGND_ExIDs = set(df_post_WNGD['Examiner_ID'])
   
    
    # Some values are strings, so must use equality rather than inequalities ><    
    pre_WGND_male_threshold = set(not_classified.loc[(not_classified['Male%']==97) | (not_classified['Male%']==96) | (not_classified['Male%']==95)]['Examiner_ID'])
    pre_WGND_female_threshold = set(not_classified.loc[(not_classified['Female%']==96) | (not_classified['Female%']==95)]['Examiner_ID'])
    pre_WGND_lowerThreshold = pre_WGND_male_threshold|pre_WGND_female_threshold 
    df_lowerThreshold = not_classified[not_classified['Examiner_ID'].isin(pre_WGND_lowerThreshold)].copy()
    
    ## Gathering First Name %
    frequencies = []
    for spelling in list(gender_country_classifiedDf['Key_Top_Spelling']):
        ex_id_key = spelling.split(",")[0] #10007
        if ex_id_key in top_ID_count:
            
            frequencies.append((top_ID_count[ex_id_key][1],top_ID_count[ex_id_key][2]))
        else:
            print("No Freq Data for:", ex_id_key) # should not enter here
    firstname_weights = [round(element[0]/element[1],2) for element in frequencies]
    gender_country_classifiedDf.insert(2, 'FirstName%', firstname_weights)
    
    ## Gathering First Name
    firstnames_ls = []
    for element in list(gender_country_classifiedDf['Key_Top_Spelling']):
        val = element.split(",")[1]
        firstnames_ls.append(val)
    gender_country_classifiedDf['FirstName'] = firstnames_ls
    
    ## Gathering Last Name 
    lastnames_ls = []
    for element in list(gender_country_classifiedDf['Key_Top_Spelling_LastName']):
        val = element.split(",")[1]
        lastnames_ls.append(val)
    gender_country_classifiedDf['LastName'] = lastnames_ls
    
    finalClassified_preWGND = gender_country_classifiedDf.rename(columns={'TopCountry': 'IBM Top Country',
                                                                          'Female%':'IBM Female %',
                                                                          'Male%':'IBM Male %','SuperCulture':'IBM_Culture'})
    
    # Matches found in just WGND                                                                   
    finalClassified_preWGND = finalClassified_preWGND.loc[:,['Examiner_ID','FirstName','FirstName%','IBM Female %','IBM Male %','LastName','IBM Top Country','IBM_Culture']].copy()
    
    ## Adding in Last Name % 
    test_all_matches = finalClassified_preWGND
    test_all_matches['Key'] = test_all_matches['Examiner_ID']+","+test_all_matches['LastName']  
    frequencies = []
    for spelling in list(test_all_matches['Key']): # Grabbing Frequency of "Top Last Name" Last Names from our Hash Map
        ex_id_key = spelling.split(",")[0] #10007
        if ex_id_key in top_ID_count_last:
            frequencies.append((top_ID_count_last[ex_id_key][1],top_ID_count_last[ex_id_key][2]))
        else:
            print("No Freq Data for:", ex_id_key)
    # Adding Frequency of "Top Last Name" Last Names
    lastname_weights = [round(element[0]/element[1],2) for element in frequencies]
    test_all_matches['LastName%'] = lastname_weights
    test_all_matches = test_all_matches.drop(columns=['Key'])
    
    finalClassified_preWGND.insert(8, 'WGND Gender', "N/A")   
    finalClassified_preWGND = finalClassified_preWGND.loc[:,['Examiner_ID','FirstName','FirstName%','IBM Female %','IBM Male %','LastName','LastName%','IBM Top Country','IBM_Culture','WGND Gender']]
    
    finalClassified_postWGND = df_post_WNGD
    finalClassified_postWGND.insert(8, 'WGND Gender', "N/A")
    finalClassified_postWGND = finalClassified_postWGND.loc[:,['Examiner_ID','FirstName','FirstName%','IBM Female %','IBM Male %','LastName','LastName%','IBM Top Country','IBM_Culture','WGND Gender']].copy()
    
    
    finalClassified_preWGND = finalClassified_preWGND.rename(columns={'Examiner_ID': 'id'})  
    finalClassified_postWGND = finalClassified_postWGND.rename(columns={'Examiner_ID': 'id'})  
    
    
    #### Concatenate Rows of full matches before WGND and after WGND
    all_matches = pd.concat([finalClassified_preWGND,finalClassified_postWGND],ignore_index=True)
    all_matches.to_csv(filename_FullMatches, sep=',', encoding='utf-8',index=False) # $$$$ Export here
    

    
    ##########################################################################################
    #                       Master Files
    ##########################################################################################
    wgnd_genders = list(all_matches['WGND Gender'])
    IBM_males = list(all_matches['IBM Male %'])
    IBM_females = list(all_matches['IBM Female %'])
    
    WGNDandIBM_Gender = []
    
    for row in range(len(all_matches)):
        try:
            if wgnd_genders[row] == "M" or IBM_males[row] >= 95:
                WGNDandIBM_Gender.append("Male")
            elif wgnd_genders[row] == "F" or IBM_females[row] >= 95:
                WGNDandIBM_Gender.append("Female")
            else:
                WGNDandIBM_Gender.append("N/A")
                
        except:
            if wgnd_genders[row] == "M":
                WGNDandIBM_Gender.append("Male")
            elif wgnd_genders[row] == "F":
                WGNDandIBM_Gender.append("Female")
            else:
                WGNDandIBM_Gender.append("N/A")
                
    all_matches['Overall Gender'] = WGNDandIBM_Gender
    
    # Extracting First Word and adding as Column 
    ls_WGND_first_Names = []
    for firstname in list(WGND_row_culture['FirstName']):
        
        firstname = firstname.split(" ")[0]
        ls_WGND_first_Names.append(firstname)
    
    WGND_row_culture['First_Word'] = ls_WGND_first_Names
    
    
    # ID + Name Key for 
    str_id_ls = list(WGND_row_culture['ExaminerID'])
    str_IDs = []
    for ex_id in str_id_ls:
        str_IDs.append(str(ex_id))
    
    ls_key = []
    ls_firstwords = list(WGND_row_culture['First_Word'])
    for i in range(len(str_IDs)):
        key = str_IDs[i]+","+ls_firstwords[i]
        ls_key.append(key)
    
    WGND_row_culture['key'] = ls_key

    # Name + Country Code Key for WGND
    codes_WGND = []
    no_code_WGND = []
    allcountries = list(WGND_row_culture['Country 1'])
    
    for country in range(len(allcountries)):
        if allcountries[country].upper() in res:
            codes_WGND.append(res[allcountries[country].upper()])
        else:
            codes_WGND.append("No Country WGND Code")
            no_code_WGND.append(allcountries[country])
    
    WGND_row_culture['country_code'] = codes_WGND
    WGND_row_culture['Name_Country_Key'] = WGND_row_culture['First_Word']+ "," + WGND_row_culture['country_code'] 
    
    
    # Merging All Rows in Examiner Data with with WGND Map 
    allWGND_Merge = pd.merge(WGND_row_culture, wgnd_map, left_on='Name_Country_Key',right_on='First_Name_Country_Key',how='left')      
    
    all_rows_genders = allWGND_Merge.loc[(allWGND_Merge['gender']=="F") | (allWGND_Merge['gender']=="M")].copy()    
    
    IBM_Country = list(allWGND_Merge['Country 1'])
    IBM_Culture = list(allWGND_Merge['super_culture'])
    WGND_Genders = list(allWGND_Merge['gender'])

    Master_file = clean_df_gender.loc[:,'ExaminerID':' Male %'].copy()
    Master_file.head()
    Master_file['IBM_Country'] = IBM_Country
    Master_file['IBM_Culture'] = IBM_Culture
    
    Master_file['WGND_Gender'] = WGND_Genders
    Master_file = Master_file.drop(columns=['Classification Confidence', 'Given Name Confidence', 'Surname Confidence'])
    Master_file_export = Master_file.rename(columns={'ExaminerID':'id','FirstName':'FirstName','Female %' : 'IBM Female %', ' Male %': 'IBM Male %', 
                                                 'LastName':'LastName','IBM_Country':'IBM Top Country','WGND_Gender':'WGND Gender'}) 
    
    ##################################### Grabbing Frequency of "Top Last Name" Last Names from our Hash Map
    # Key column for "ID,first" - to perform Assignment of Gender
    test_Master_file_export = Master_file_export
    test_Master_file_export['Examiner_ID_String'] = test_Master_file_export['id'].apply(str).replace('\.0', '', regex=True)
    test_Master_file_export['Key_Last'] = test_Master_file_export['Examiner_ID_String'] +","+ test_Master_file_export['LastName']
    
    frequencies = []
    for spelling in list(test_Master_file_export['Key_Last']):
        ex_id_key = spelling.split(",")[0] #10007 
        try:     
            # IF our LawyerID exists in Patent data
            if ex_id_key in top_ID_count_last:
                # This is where you'll add the: numerator for last name count AND denominator (or total for ID)
                frequencies.append((top_ID_count_last[ex_id_key][1],top_ID_count_last[ex_id_key][2]))            
            # LawyerID Does not exist Patent Data
            else:
                frequencies.append((0,1))
    
        except:
            frequencies.append((0,1))                           
    
    # Adding Frequency of "Top Last Name" Last Names
    lastname_weights = [round(element[0]/element[1],2) for element in frequencies]
    
    weights_rounded = []
    for i in range(len(frequencies)):
        try:
            val = round(frequencies[i][0]/frequencies[i][1],2)
            weights_rounded.append(val)
        except:
            print("should not enter here")
    
    test_Master_file_export['LastName%'] = weights_rounded
    test_Master_file_export = test_Master_file_export.drop(columns=['Key_Last'])
    
    #################################### Grabbing Frequency of "Top First Name" Last Names from our Hash Map
    # Keys for Frequqencies
    test_Master_file_export['Key_First'] = test_Master_file_export['Examiner_ID_String']+','+test_Master_file_export['FirstName']
    frequencies = []
    for spelling in list(test_Master_file_export['Key_First']):
        ex_id_key = spelling.split(",")[0] #10007
        try:        
            # IF our LawyerID exists in Patent data
            if ex_id_key in top_ID_count:
                # This is where you'll add the: numerator for last name count AND denominator (or total for ID)
                frequencies.append((top_ID_count[ex_id_key][1],top_ID_count[ex_id_key][2]))
            # LawyerID Does not exist Patent Data
            else:
                frequencies.append((0,1))
        except:     
            frequencies.append((0,1))
    
    # Adding Frequency of "Top First  Name" Last Names
    lastname_weights = [round(element[0]/element[1],2) for element in frequencies]
    weights_rounded = []
    for i in range(len(frequencies)):
        try:
            val = round(frequencies[i][0]/frequencies[i][1],2)
            weights_rounded.append(val)
        except:
            print("should not enter here")
            
    test_Master_file_export['FirstName%'] = weights_rounded
    test_Master_file_export = test_Master_file_export.drop(columns=['Key_First'])
    Master_file_export = test_Master_file_export.loc[:,['id','FirstName','FirstName%','IBM Female %','IBM Male %','LastName','LastName%','IBM Top Country','IBM_Culture','WGND Gender']]
    Master_file_export.to_csv(filename_Master, sep=',', encoding='utf-8',index=False) # $$$$ Export here
    return Master_file_export,all_matches
    


def main():   
######################## 1) IBM Data: Convert to DataFrame (return additional master copy)

    #### Examiner Comment ####
    examiner_file = "ExaminerDirectory_New_Output3.csv"
    person_type = "Examiners" 
    filename_FullMatches, filename_Master = "Examiners_FullMatches_All.csv","Examiners_Master.csv" # output file names
    clean_df_master,clean_df_gender,clean_df_country = file_reader(examiner_file, person_type )
    
    # ### Lawyer Comment ####
    # lawyer_file = "LawyerDirectory_New_Output3.csv"
    # person_type = "Lawyers"
    # filename_FullMatches, filename_Master = "Lawyers_FullMatches_All.csv","Lawyers_Master.csv" # output file names
    # clean_df_master,clean_df_gender,clean_df_country = file_reader(lawyer_file, person_type )



    # Row level (Genders): Assign Male or Female to every Row based on the defined threshold against IBM's GNR Gender confidence score
    IBM_threshold = 95
    clean_df_gender = IBM_GenderCutoff(clean_df_gender,IBM_threshold)
    
    # Row level (Country/Culture): 
    row_culture,WGND_row_culture = IBM_SuperCulture(clean_df_country) # Return additional for WGND assignments
    
######################## 2) Patent Data: Gather Name %  
    
    ### Examiner Comment ####
    Examiner_patentfile = "ExaminerPatentMap.csv" 
    # Gather relative frequencies of a first/last name in the Patent File, for a given examiner/lawyer ID
    # If Examiners: Aggregate Frequencies of  primary + assistant 
    examiner_ID_count,examiner_ID_count_last = patentdata_map(Examiner_patentfile)
    

    # #### Lawyer Comment ####
    # Lawyer_patentfile = "LawyerPatentMap.csv" 
    # # Gather relative frequencies of a first/last name in the Patent File, for a given examiner/lawyer ID
    # # If Examiners: Aggregate Frequencies of  primary + assistant
    # examiner_ID_count,examiner_ID_count_last  = patentdata_map(Lawyer_patentfile) 

######################## 3) Merge: Patent Counts + IBM Data 
    assign_type_gender = "gender" # First name analysis 
    assign_type_country = "country"  # First name analysis     

    # This Merges the relative frequency of a first name , with the their IBM Gender confidence scores
    Examiner_pantentfreq_IBMgender = apply_patentfreq(examiner_ID_count,clean_df_gender,assign_type_gender)
    # This Merges the relative frequency of a last name , with the their IBM Country data
    Examiner_pantentfreq_IBMgender_lastname = apply_patentfreq(examiner_ID_count_last,clean_df_country,assign_type_country) 
    
######################## 4) Collpapsing ID: selecting a name within ID

    # Pick top name within ID by: using the most frequent unambigious names, that also meets frequency threshold    
    # First Name (Gender)
    firstName_freq_threshold = .40 # that occured atleast 40% in the patent data (relative to it's ID)  
    final_df,classified,not_classified,top_ID_count = collapse_id(Examiner_pantentfreq_IBMgender,assign_type_gender,firstName_freq_threshold)
    # Last Name (Country)
    lastName_freq_threshold = .90
    final_df_culture,classified_last,not_classified_last,top_ID_count_last = collapse_id(Examiner_pantentfreq_IBMgender_lastname,assign_type_country,lastName_freq_threshold)

######################## 5) Merge: Gender + Country data ######## 

    # Filter which names have both Gender and Country data frame IBM assigned   
    gender_country_classifiedDf,WGND_df = ibm_classified(classified,classified_last,not_classified)    
    
######################## 6) WGND Data: Examiners where IBM could only classify Country, use WGBD to assign Genders

    df_post_WNGD = WGND_assignGender(WGND_df)
    print(len(df_post_WNGD))

######################## 7) Export Data: Formatting, Filtering, and Exporting output tables

    Master_file_export,all_matches = export_files(gender_country_classifiedDf,top_ID_count,not_classified,df_post_WNGD,top_ID_count_last,WGND_row_culture,clean_df_gender,wgnd_map,filename_FullMatches, filename_Master )

    #### Return for Variable Testing
    return Master_file_export,all_matches



# Start Time
t0 = time.time()

Master_file_export,all_matches = main()

# End Time
t1 = time.time()
total = t1-t0
print(total)  