//  CompleteAnalysis.java - demonstrate complete name analysis with NameWorks
//
//  Licensed Materials - Property of IBM
//  "Restricted Materials of IBM"
//  5724-Q20
//  © Copyright IBM Corp. 2010

import java.util.List;
import java.util.Set;

import java.io.*;
import java.util.Scanner;


import com.ibm.gnr.core.*;
import com.ibm.gnr.nwa.Analytics;

public class CompleteAnalysisNames
{
	//  load native code module
	static { System.loadLibrary("analytics"); }

	public static void main(String[] args) throws Throwable
	{
		//  input encoding
		String encoding = "UTF-8";
		//  minimum parse confidence
		int threshold = 70;
		//  maximum number of variants to show
		int variants = 5;
		//  maximum number of countries to show
		int countries = 5;

		//  create a NW Analytics object
		Analytics analytics = new Analytics("analysis.config");
		
		//  loop over input
		BufferedReader input = new BufferedReader(
		                           new InputStreamReader(System.in, encoding));
				
//		// Input file
//		String fileName = "ExaminerDirectory.csv"; // Comment Examiner
		
//		//Output File 
//		String fileOutName = "ExaminerDirectory_New_Output3.csv"; // Comment Examiner
		 
		String fileName = "LawyerDirectory.csv"; // Comment Lawyer
		String fileOutName = "LawyerDirectory_New_Output3.csv"; // Comment Lawyer 
		
		
		File file = new File(fileName);
		File fileOut = new File(fileOutName);
		
		
		// Calculating columns from Input file 
		// Appending to Output File
		try {
            // Input
			FileReader fr = new FileReader(file);
            BufferedReader br = new BufferedReader(fr);
            
            // Output
            FileWriter fw = new FileWriter(fileOut, true);
            BufferedWriter bw = new BufferedWriter(fw);
            
            //Write Headers to output file

         // Comment Examiner
//            bw.write("ExaminerID,FirstName,LastName,ID,Classification Confidence,Given Name Confidence"
//            		+ ",Surname Confidence,Female %, Male %,"
//            		+ "Country 1,Country 1 Frequency,Country 1 Confidence,Country 1 Score,"
//            		+ "Country 2,Country 2 Frequency,Country 2 Confidence,Country 2 Score,"
//            		+ "Country 3,Country 3 Frequency,Country 3 Confidence,Country 3 Score,"
//            		+ "Country 4,Country 4 Frequency,Country 4 Confidence,Country 4 Score,"
//            		+ "Country 5,Country 5 Frequency,Country 5 Confidence,Country 5 Score,"
//            		+ "Top Culture\n");
            
         // Comment Lawyer
            bw.write("ExaminerID,FirstName,LastName,Classification Confidence,Given Name Confidence"
            		+ ",Surname Confidence,Female %, Male %,"
            		+ "Country 1,Country 1 Frequency,Country 1 Confidence,Country 1 Score,"
            		+ "Country 2,Country 2 Frequency,Country 2 Confidence,Country 2 Score,"
            		+ "Country 3,Country 3 Frequency,Country 3 Confidence,Country 3 Score,"
            		+ "Country 4,Country 4 Frequency,Country 4 Confidence,Country 4 Score,"
            		+ "Country 5,Country 5 Frequency,Country 5 Confidence,Country 5 Score,"
            		+ "Top Culture\n");

            
            String str; //String for each row
            while((str = br.readLine()) != null) 
            {
				String[] values = str.split(","); // Converting first name and last name into array
				
				//To just search: first name and last name
				String[] non_ID_values = new String[2]; 
//				for (int i = 1; i < values.length-1;i++) { // Comment Examiner 
				for (int i = 1; i < values.length;i++) { // Comment Lawyer 
					
					non_ID_values[i-1] = values[i];
				}
				// This is First name and Last name 
				String fullString = String.join(" ", non_ID_values);
				
            	
            	for ( ;; )
    				{
    					if ( analytics.categorize(fullString).getNameCategories().contains(NameCategory.PERSONAL) )
    					{
    						// For each conjoined name 
    						// Full Name = First name + Last Name
    						for ( AnalysisAlternate aa : analytics.analyze(fullString, threshold, variants, countries) )
    						{	
    							// For each possible parse (all name combinations in first name column)
    							// Analysis Name is all words in first or last name (ex. if Middle name exists, iterates 2x)
    							for ( AnalysisName an : aa.getParses() )
    							{

    								// This will hold all calculated fields (i.e. Gender and Country data)
    								StringBuffer sb = new StringBuffer("");
    								
    								// Classification confidence
    								sb.append(an.getConfidence() + ",");
								
									
    								
    								
//%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% First Name Analysis %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    								AnalysisField field = an.getGivenName();
    								
    								// Name from file 
    								String FirstName_Input = non_ID_values[0];
    								FirstName_Input = FirstName_Input.toUpperCase();
    	
    								// Name from parse
    								String Parse_Output = an.getGivenName().getText().toString();
    								
    								
    								/// Begin: If parse combo (First + Middle) is equal to our input (First + Middle)
    								if (Parse_Output.equals(FirstName_Input)) {
        
    									// If name contains more than one word 
    									// Use first word (as Parse can only be one word and parse contains gender data) 
    									if (Parse_Output.contains(" ")) {
    										
    										// First word so we can reference (First)
    										String just_first_name = Parse_Output.substring(0, Parse_Output.indexOf(" "));
    										
    	    								// Counter for format
    										int ap_counter = 0;
    										
    										// For each word in First Name 
    	    								for ( AnalysisPhrase ap : field.getAnalysisPhrases() ) {    									
    	    									
    	    									
    	    									// GivenName, SureName, Gender Frequency based off AnalysisPhrase (one word)
    	    									ParsePhrase pp = ap.getParsePhrase();
    	    									
    	    									// If middle name exists we can concatenate (ex. Mary Kate) 
    	    									// There can be a given name (Jung Won) and we are saying: Jung Won == Jung
    	    									if (pp.getText().equals(just_first_name)) { // AnalysisPhrase must equal the first word of first name
        	    									sb.append(pp.getGivenNameFactor() + ",");
        	    									sb.append(pp.getSurnameFactor() +  ",");
    	    										
        	    									// Gender Likelihood
        	    									GenderData gd = ap.getGenderData();
//        	    									if ( gd.getFrequency() > 0 ) {
        		    										sb.append(gd.getFemalePercent() + ",");
        		    										sb.append(gd.getMalePercent() +  ",");
//        	    									}
        	    									
//        	    									else {
//        	    										sb.append("No Female %"+",");
//        	    										sb.append("No Male %"+",");
//        	    									}
        	    									ap_counter++;
        	    									break; // No analysis on middle name because of break here
    	    									}
    	    								}
    	    								
    	    								// While loop to just format if the name was ambiguous (based off counter)
    	    								while (ap_counter < 1) {
    	    									sb.append(",");
    	    									sb.append(",");
    	    									sb.append(",");
    	    									sb.append(",");
    	    									ap_counter++;
    	    								}
    									}
    								
    									// If First Name contains exactly one word
    									else {
        									int ap_counter = 0;
        									// For word in First Name 
    	    								for ( AnalysisPhrase ap : field.getAnalysisPhrases() ) {
    	    									
    	    									// GivenName, SureName, Gender Frequency based off AnalysisPhrase (one word)
    	    									ParsePhrase pp = ap.getParsePhrase();
    	    									sb.append(pp.getGivenNameFactor() + ",");
    	    									sb.append(pp.getSurnameFactor() +  ",");
    
    	    									// Gender Likelihood
    	    									GenderData gd = ap.getGenderData();
//    	    									if ( gd.getFrequency() > 0 ) { // AnalysisPhrase must equal the first word of first name
    		    										sb.append(gd.getFemalePercent() + ",");
    		    										sb.append(gd.getMalePercent() +  ",");
    		    										
//    	    									} 
//    	    									else {
//    	    										sb.append("No Female %"+",");
//    	    										sb.append("No Male %"+",");
//    	    									}
    	    									ap_counter++;
    	    									break; // No analysis on middle name because of break here
    	    									
    	    								}
    	    								// While loop to just format if the name was ambiguous (based off counter)
    	    								while (ap_counter < 1) {
    	    									sb.append(",");
    	    									sb.append(",");
    	    									sb.append(",");
    	    									sb.append(",");
    	    									ap_counter++;
    	    								}
    										
    									}

    								} // End: If parse combo (First + Middle) is equal to our input (First + Middle)
    								
//%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Last Name Analysis %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    								// Last Name from file 
    								String LastName_Input = non_ID_values[1];
    								LastName_Input = LastName_Input.toUpperCase();
    								
    								// Last Name from parse
    								AnalysisField last_name_field = an.getSurname();
    								String Parse_Output_last = an.getSurname().getText().toString();
	
    								/// Begin: If parse combo (Last + Last Additional word) is equal to our input (Last + Last Additional word)
    								if (Parse_Output_last.equals(LastName_Input)) {
    									
    									// If name contains more than one word, use first word 
    									// As Parse can only be one word and parse contains gender data 
	    								if (last_name_field.getText().contains(" ")) {
	    									String just_last_name = Parse_Output_last.substring(0, Parse_Output_last.indexOf(" "));
	    									
	    									// For each word in Last Name 
	    									for ( AnalysisPhrase ap_last : last_name_field.getAnalysisPhrases() ) {
	        									
	        									GenderData gd = ap_last.getGenderData();
	        									ParsePhrase pp = ap_last.getParsePhrase();
	        									if (pp.getText().equals(just_last_name)) { // AnalysisPhrase must equal the first word of last name
	        										
	        										int country_counter = 0;
	    	    									// Country Frequency and Confidence (Based off Last Name)
	    											for ( CountryElement ce : ap_last.getCountryElements() ) {
	    												country_counter++;
	    												sb.append(LocalText.text(ce.getCountry()) + ",");
	    												sb.append(ce.getFrequency() + ",");
	    												sb.append(ce.getConfidence() + ",");
	    												sb.append((ce.getFrequency()*ce.getConfidence()) + ",");
	    											}
	    											// Formatting for Culture to append in correct column
	    											while (country_counter < 5) {
	    												sb.append(",");
	    												sb.append(",");
	    												sb.append(",");
	    												sb.append(",");
	    												country_counter++;
	    											}
//	    											

	    											
	    											// Top Culture (Based off Last Name)
	    											try
	    											{
	    												sb.append(LocalText.text(ap_last.getCultureSet()));
	    											}
	    											catch ( InvalidCultureSetException e )
	    											{
	    												System.err.println("Invalid culture set");
	    											}
	    											
		    									}

	        								}
	    									
	    								}
	    								
	    								// If name contains exactly one word 
	    								// as Parse can only be one word and parse contains gender data 
	    								else {
	    									// For word in Last Name 
	    									for ( AnalysisPhrase ap_last : last_name_field.getAnalysisPhrases() ) {
	        									GenderData gd = ap_last.getGenderData();
	        									int country_counter = 0;
	    	    									
	        									// Country Frequency and Confidence (Based off Last Name)
    											for ( CountryElement ce : ap_last.getCountryElements() ) {
    												country_counter++;
    												sb.append(LocalText.text(ce.getCountry()) + ",");
    												sb.append(ce.getFrequency() + ",");
    												sb.append(ce.getConfidence() + ",");
    												sb.append((ce.getFrequency()*ce.getConfidence()) + ",");
    											}
    											// Formatting for Culture to append in correct column
    											while (country_counter < 5) {
    												sb.append(",");
    												sb.append(",");
    												sb.append(",");
    												sb.append(",");
    												country_counter++;
    											}
//	    															
	    											
    											// Top Culture (Based off Last Name)
    											try
    											{
    												sb.append(LocalText.text(ap_last.getCultureSet()));
    											}
    											catch ( InvalidCultureSetException e )
    											{
    												System.err.println("Invalid culture set");
    											}	
	    									}
	    								}
    								}

    								
// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%   Finished gather data >> write to CSV %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    								sb.append("\n"); // New row for new name
    						
    								// Print once per person (not once per parse)
    								if (Parse_Output.equals(FirstName_Input)){
    									// All fields from API
    									String analysis = sb.toString(); 
        								
        								// Original Data
        								for (String name : values) {
        									bw.write(name);
        									bw.write(",");
        								}
        								bw.write(analysis);
    								}
    								

    							}
    							break;
    						}
    					}
    					else {

//    						System.out.println("**************************");
//    						System.out.println("Finished Analysis on: " + fullString);
//    						System.out.println("**************************");
    					}
    					break;
    				}
           
            }
            System.out.println("Done");

            br.close();
            fr.close();
            bw.close();
       }

       catch(IOException e) {
    	   e.printStackTrace();
    	   }
	
	}
//###########################################################################################	
}
