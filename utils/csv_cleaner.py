import pandas as pd
import numpy as np

# --- 1. USER CONFIGURATION: PLEASE EDIT THESE VALUES ---

# Specify the full path to your input Excel file
# The 'r' before the string is important for Windows paths.
input_excel_file = r'D:\Projects\OHCM-HR\Data\Faculty Details UMT.xlsx' 

# Specify the name for the final output CSV file
output_csv_file = 'cleaned_faculty_data_final.csv'


# --- 2. SCRIPT LOGIC (No changes needed below unless warnings appear) ---

def process_qualifications(df, id_vars, qual_map, category_name):
    """Helper function to process one set of qualification columns."""
    
    current_id_vars = [col for col in id_vars if col in df.columns]

    original_title_col = qual_map.get('original_title')
    if not original_title_col or original_title_col not in df.columns:
        return None
        
    original_qual_cols = [qual_map.get(k) for k in ['original_title', 'original_institution', 'original_country', 'original_year'] if qual_map.get(k) in df.columns]
    
    if original_title_col not in original_qual_cols:
        return None

    subset_df = df[current_id_vars + original_qual_cols].copy()
    
    temp_rename_map = {
        qual_map.get('original_title'): 'qualification_title_temp',
        qual_map.get('original_institution'): 'institution_temp',
        qual_map.get('original_country'): 'country_temp',
        qual_map.get('original_year'): 'year_temp'
    }
    subset_df.rename(columns={k: v for k, v in temp_rename_map.items() if k}, inplace=True)

    subset_df['Category (Educational, Professional)'] = category_name
    subset_df.dropna(subset=['qualification_title_temp'], inplace=True)
    
    return subset_df


def clean_and_transform_data(input_file, output_file):
    """
    Reads a wide-format Excel file, transforms it into a long format with one row
    per qualification, cleans the data, and saves it to a CSV file.
    """
    try:
        df = pd.read_excel(input_file)
        print("Successfully read the Excel file.")
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found. Please check the file name and path.")
        return
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        return

    # Define the expected column names from your Excel file.
    # This list contains corrections for common typos.
    id_vars_expected = [
        'Title', 'Code', 'Email', 'Academic Designation', 'Administrative Designation', 'Status',
        'Date of Joining', 'Teaching Experience at Joining', 'Professional Experience at joining',
        'Employee Name', "Father's Name / Husband'sName", # Using standard apostrophe
        'Sex', 'Date of Birth', 'Mobile #', 'Email 2', 'CNIC #', 'CNIC Expiry Date', 'Marital Status', 
        'Blood Group', 'Date of Marriage', 'No Of Dependents' # Corrected to plural 'Dependents'
    ]
    
    # --- DIAGNOSTIC CHECK ---
    # This code checks if any of the expected columns are missing from your file.
    actual_columns = df.columns
    missing_columns = [col for col in id_vars_expected if col not in actual_columns]
    
    if missing_columns:
        print("\n--- WARNING: The following columns were not found in your Excel file ---")
        for col in missing_columns:
            print(f"- '{col}'")
        print("--------------------------------------------------------------------------")
        print("Please check for typos or extra spaces in these column names in your Excel file or in the 'id_vars_expected' list in the script.\n")

    # The script will only use the columns that it actually finds.
    id_vars = [var for var in id_vars_expected if var in actual_columns]

    # Defines the qualification columns to search for. Adjust if pandas renames duplicates (e.g., 'Year 1.1')
    qualification_sets = [
        ( {'original_title': 'Qualification 1', 'original_institution': 'University 1', 'original_country': 'Country 1', 'original_year': 'Year 1'}, 'Educational' ),
        ( {'original_title': 'Qualification 2', 'original_institution': 'University 2', 'original_country': 'Country 2', 'original_year': 'Year 2'}, 'Educational' ),
        ( {'original_title': 'Qualification 3', 'original_institution': 'University 3', 'original_country': 'Country 3', 'original_year': 'Year 3'}, 'Educational' ),
        ( {'original_title': 'Professional Qualification 1', 'original_institution': 'University/Institute 1', 'original_country': 'Country 1.1', 'original_year': 'Year 1.1'}, 'Professional' ),
        ( {'original_title': 'Professional Qualification 2', 'original_institution': 'University/Institute 2', 'original_country': 'Country 2.1', 'original_year': 'Year 2.1'}, 'Professional' )
    ]

    all_quals_dfs = []
    print("Transforming data from wide to long format...")
    for qual_map, category_name in qualification_sets:
        processed_df = process_qualifications(df, id_vars, qual_map, category_name)
        if processed_df is not None and not processed_df.empty:
            all_quals_dfs.append(processed_df)
    
    if not all_quals_dfs:
        print("Error: No qualification data could be processed. Please check your qualification column names.")
        return

    final_df = pd.concat(all_quals_dfs, ignore_index=True, sort=False)
    print("Transformation complete.")
    
    print("Applying pre-processing and data type conversions...")

    # Renames all found columns to your desired final names.
    final_rename_map = {
        'Title': 'Faculty Title', 'Email': 'University Email', 'Date of Joining': 'Date of Joining',
        'Teaching Experience at Joining': 'Teaching Experience', 'Professional Experience at joining': 'Professional Experience',
        'Employee Name': 'Full Name', "Father's Name / Husband'sName": 'Father/Husband Name',
        'Sex': 'Sex', 'Date of Birth': 'Date of Birth', 'Mobile #': 'Phone Number',
        'Email 2': 'Personal Email', 'CNIC #': 'CNIC', 'CNIC Expiry Date': 'CNIC Expiry',
        'Marital Status': 'Martial Status', 'Blood Group': 'Blood Group',
        'Date of Marriage': 'Date of Marriage', 'No Of Dependents': 'No Of Dependent',
        'Academic Designation': 'Academic Designation', 'Administrative Designation': 'Administrative Designation',
        'Status': 'Status', 'qualification_title_temp': 'Qualification Title',
        'institution_temp': 'Institution', 'country_temp': 'Country', 'year_temp': 'Year'
    }
    final_df.rename(columns=final_rename_map, inplace=True)

    if 'Full Name' in final_df.columns:
        name_parts = final_df['Full Name'].astype(str).str.split(' ', n=1, expand=True)
        final_df['First Name'] = name_parts[0]
        final_df['Last Name'] = name_parts[1]
        final_df.drop(columns=['Full Name'], inplace=True)
    else:
        final_df['First Name'] = ''
        final_df['Last Name'] = ''

    # --- DATA TYPES AND NULLS SECTION ---

    date_columns = ['Date of Joining', 'Date of Birth', 'CNIC Expiry', 'Date of Marriage']
    for col in date_columns:
        if col in final_df.columns:
            final_df[col] = pd.to_datetime(final_df[col], errors='coerce').dt.strftime('%Y-%m-%d').replace('NaT', '')

    experience_columns = ['Teaching Experience', 'Professional Experience', 'Code']
    for col in experience_columns:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype(int)

    other_numeric_cols = ['No Of Dependent', 'Year']
    for col in other_numeric_cols:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').astype('Int64')

    # Cleans all remaining text-based columns, ensuring 'Code' is treated as text.
    for col in final_df.select_dtypes(include=['object']).columns:
        final_df[col] = final_df[col].astype(str).str.strip().replace('nan', '')

    print("Data cleaning complete.")

    # --- FINALIZE AND SAVE CSV ---
    
    # This list defines the exact order of columns in your final CSV file.
    final_columns_order = [
        'Faculty Title', 'Code', 'First Name', 'Last Name', 'Father/Husband Name', 'Sex', 
        'Date of Birth', 'Phone Number', 'Personal Email', 'CNIC', 'CNIC Expiry',
        'Martial Status', 'University Email', 'Academic Designation', 
        'Administrative Designation', 'Status', 'Date of Joining',
        'Teaching Experience', 'Professional Experience',
        'Blood Group', 'Date of Marriage',
        'No Of Dependent', 'Category (Educational, Professional)', 'Qualification Title', 'Institution', 'Country', 'Year'
    ]
    
    # The script will only include columns that actually exist after processing.
    existing_final_columns = [col for col in final_columns_order if col in final_df.columns]
    final_df = final_df[existing_final_columns]
    
    try:
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Successfully created the cleaned CSV file: '{output_file}'")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")

# --- Run the main function ---
if __name__ == "__main__":
    clean_and_transform_data(input_excel_file, output_csv_file)