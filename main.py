
# Finish: Clean this up and import from "modulesImport.py"
import  pandas as pd
import numpy as np
from resources.superCultureMap import culture_dict
import time
from collections import defaultdict
import regex as re


class GenderRaceAnalysis:
    def __init__(self,fileType):
        assert fileType == "E" or fileType == "L", ' Must indicate Examiners or Lawyers by passing, either: "E" or "L" '
        self.femaleThreshold = self.maleThreshold = 95

        self.superCultureMap = culture_dict

        if fileType == "E":
            self.fileType = "Examiners"
            self.filePathIbm = "data/ibmOuputs/ExaminerDirectory_New_Output3.csv"
            self.filePathPatent = "data/patentData/ExaminerPatentMap.csv"
            # self.patentDataPath = "" # Finish: add my .db file here
            self.patentDict = self.getPatentData()
        elif fileType == "L":
            self.fileType = "Lawyers"
            self.filePathIbm = "data/ibmOuputs/LawyerDirectory_New_Output3.csv"
            self.filePathPatent = "data/patentData/LawyerPatentMap.csv"
            # self.patentDataPath = "" # Finish: add my .db file here
            self.patentDict = self.getPatentData()

        self.genderDf,self.countryDf = self.readFile()
        self.IBM_GenderCutoff(self.genderDf,self.femaleThreshold,self.maleThreshold)
        self.IBM_SuperCulture()
        self.mergePatentIbm()
        
    def readFile(self):
        """
        Reads and formats IBM output files
        Returns 2 pandas dataframe for Gender and Culture Analysis
        """
        clean_df_master = pd.read_csv(self.filePathIbm).fillna("")
        clean_df_master['ExaminerFirstName_Key'] = clean_df_master['ExaminerID'].astype(str) + "," + clean_df_master['FirstName']
        clean_df_master['ExaminerLastName_Key'] = clean_df_master['ExaminerID'].astype(str) + "," + clean_df_master['LastName']

        # Dataframe for Gender
        clean_df_master.insert(9, 'Female Classification', "TBD")
        clean_df_master.insert(10, 'Male Classification', "TBD")        
        genderDf = clean_df_master[['ExaminerID','FirstName', 'LastName', 'Classification Confidence', 'Given Name Confidence', 'Surname Confidence', 'Female %',  'Female Classification',  ' Male %',  'Male Classification','ExaminerFirstName_Key','ExaminerLastName_Key',]]

        # Dataframe for Country and Culture
        clean_df_country = clean_df_master[['ExaminerID', 'FirstName', 'LastName', 'ExaminerFirstName_Key','ExaminerLastName_Key','Country 1','Top Culture', 'Unnamed: 31','Unnamed: 32', 'Unnamed: 33', 'Unnamed: 34','Unnamed: 35', 'Unnamed: 36','Unnamed: 37','Unnamed: 38', 'Unnamed: 39']]
        countryDf = clean_df_country.rename(columns={ "Unnamed: 31": "Top Culture 2"  ,"Unnamed: 32": "Top Culture 3","Unnamed: 33": "Top Culture 4","Unnamed: 34": "Top Culture 5","Unnamed: 35": "Top Culture 6","Unnamed: 36": "Top Culture 7","Unnamed: 37": "Top Culture 8","Unnamed: 38": "Top Culture 9","Unnamed: 39": "Top Culture 10"})

        return genderDf, countryDf
       
    
    def IBM_GenderCutoff(self, genderDf,thresholdFemale,thresholdMale):
        """
        Assign Gender to Rows, based on defined threshold 
        """
        genderDf['Female %'] = pd.to_numeric(genderDf['Female %'], errors='coerce')
        genderDf['Male %'] = pd.to_numeric(genderDf[' Male %'], errors='coerce')
        genderDf['Female Classification'] = [ 1 if val >= thresholdFemale else 0 for val in genderDf['Female %']]
        genderDf['Male Classification'] = [ 1 if val >= thresholdMale else 0 for val in genderDf['Male %']]
        del genderDf[' Male %'] 
    
    def IBM_SuperCulture(self):
        """
        Compresses up to 10 cultures associated with a given name into 1 super culture value
        """
        superCulturesCol = []
        for index, row in self.countryDf.loc[:, "Top Culture":"Top Culture 10"].iterrows():
            cultures = set(filter(lambda x: False if x == "" else True,row)) # filter out instances with no culuture value (ex. "Top Culture 10" column)
            superCultures = [self.superCultureMap[culture] for culture in cultures] 
            if "Ambiguous" not in superCultures and len(superCultures) == 1:
                superCulturesCol.append(superCultures[0])
            elif "Ambiguous" in superCultures or len(superCultures) > 1:
                superCulturesCol.append("No certain culture")
            else:
                superCulturesCol.append("Ambiguous")
        
        dropThese = ["Top Culture", "Top Culture 2", "Top Culture 3", "Top Culture 4", "Top Culture 5", "Top Culture 6", "Top Culture 7", "Top Culture 8", "Top Culture 9", "Top Culture 10"]
        self.countryDf.drop(columns=dropThese, axis=1, inplace=True)
        self.countryDf['super_culture'] = superCulturesCol

    def getPatentData(self):
        """
      
        """
        if self.fileType == "Examiners":

            # Finish!!!: First name only, causing problems below in mergePatentIbm() 
            # b/c I am missing lastname for cultures

            df = pd.read_csv(self.filePathPatent, dtype={"PrimaryID": 'str',"AssistantID": 'str',})
            df["Primary_FirstName_Key"] = df["PrimaryID"] + "," + df["Primary_Firstname"]
            df["AssistantFirstName_Key"] = df["AssistantID"]  + "," + df["Assistant_FirstName"]
            allExaminers = list(df["Primary_FirstName_Key"].dropna()) + list(df["AssistantFirstName_Key"].dropna())

            nameCount = defaultdict(list)
            for key in allExaminers:
                if key in nameCount:
                    nameCount[key][0] += 1
                else:
                    nameCount[key].append(1)
                    idStr = re.search('([0-9]+),.+', key)
                    if idStr: nameCount[key].append(idStr.group(1))
            return nameCount
    
    def mergePatentIbm(self):



        genderDfIbm, countryDfIbm = self.genderDf, self.countryDf
        patentDict = self.patentDict # Just for First Name search "Finish!!!"
        mergedDict_Gender = defaultdict(list)
        mergedDict_Country = defaultdict(list)
        # print(patentDict)


        print("master len: ", len(genderDfIbm))
        print("master len 2: ", len(patentDict))

        for i in range(len(genderDfIbm)):
            
            # Problem here: 
            # - currently, mergedDict_Gender's len = 39325
            # - correct, mergedDict_Gender's len = 42557

            # - currently, mergedDict_Country's len = 147 # Just for First Name search "Finish!!!"
            # - correct, mergedDict_Country's len = 29923 # Just for First Name search "Finish!!!"


            # Gender
            key = genderDfIbm['ExaminerFirstName_Key'][i]
        
            if key in patentDict:# and key not in mergedDict_Gender:
                idStr_Gender = genderDfIbm['ExaminerID'][i]
                count = patentDict[key][0]
                valFemale = genderDfIbm['Female %'][i]
                valMale = genderDfIbm['Male %'][i]
                mergedDict_Gender[key] = [count,idStr_Gender,valFemale,valMale]
            
            # # Culture
            # key_Country = countryDfIbm['ExaminerLastName_Key'][i]
            # if key_Country in patentDict:# and key_Country not in mergedDict_Country:
            #     idStr_Country = countryDfIbm['ExaminerID'][i]
            #     count = patentDict[key_Country][0]
            #     valCountry = countryDfIbm['Country 1'][i]
            #     valCulture = countryDfIbm['super_culture'][i]
            #     mergedDict_Country[key_Country] = [count,idStr_Country,valFemale,valMale]
        
        print(mergedDict_Gender['10007,RODNEY H']) 
        print(mergedDict_Gender['25812,MANUEL RIVERA'])

        print(len(mergedDict_Gender))
        # mergedDict_Gender['10007,RODNEY H'] => [4804, '10007', 0.0, 98.0] ----> non ambigious
        


def main():
    t0 = time.time()
    examinerObj = GenderRaceAnalysis("E")
    # print(f'gender df: {examinerObj.genderDf.head(1)}')
    # print(f'country df: {examinerObj.countryDf.head(1)}')

    t1 = time.time()
    print(f"time elapsed: {round(t1-t0,2)} sec")
    


main()