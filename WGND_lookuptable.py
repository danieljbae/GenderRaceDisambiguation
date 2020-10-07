# -*- coding: utf-8 -*-
"""
Created on Sun May 17 14:28:39 2020

@author: danie
"""
import pandas as pd 


wgnd_map = pd.read_csv('C:/Users/danie/Desktop/Research/Gender_Race_Disambiguation/WIPO/WIPO WGND/wgnd_ctry.csv')
wgnd_map = wgnd_map.fillna("")
wgnd_map = wgnd_map.drop(columns=['gchar12', 'gchar12','gchar1','gchar2'])
wgnd_map['First_Name_Country_Key'] = wgnd_map['name']+ "," + wgnd_map['code'] 
