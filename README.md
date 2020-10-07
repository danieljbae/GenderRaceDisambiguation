# GenderRaceDisambiguation
This project assigns geneder and culture to patent examiners and lawyers, based on patents granted in 2001-2012.

## Code overview

* IBM's Global Name Management API (used in CompleteAnalysisNames.java), which is effectively a lookup table built from culture name specific data. 
This resource was used to assign gender and culture to every name spelling, a given examiner or lawyer used within span of 11 years. 

* Selection of name spelling to represent a given examiner or lawyer can be seen in Gender_CountryCulture_Assignment_v2.py

## Example of Distrubutions 

Cultural distributions on Examiners:

![alt text](https://github.com/danieljbae/GenderRaceDisambiguation/blob/master/Examiners_Cultural_Dist.PNG)

Some of the analysis performed on Examiners, to assign thresholds:

![alt text](https://github.com/danieljbae/GenderRaceDisambiguation/blob/master/Examiners_FirstName.PNG)
