import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

class PersonDataPipeline:
    """
    A comprehensive data cleaning pipeline for person details.
    Processes a raw DataFrame and prepares it for database insertion.
    """
    
    def __init__(self):
        self.logger = self._setup_logger()
        
        # Column mapping configuration from raw file to intermediate names
        self.column_mapping = {
            'Employee Name': 'Employee Name',
            "Father's Name / Husband'sName": "Father's Name / Husband'sName",
            'Sex': 'Sex',
            'Email': 'Email',
            'CNIC #': 'CNIC #',
            'CNIC Expiry Date': 'CNIC Expiry Date',
            'Date of Birth': 'Date of Birth',
            'Mobile #': 'Mobile #',
            'Blood Group': 'Blood Group',
            'Marital Status': 'Marital Status',
            'No Of Dependents': 'No Of Dependents',
            'Date of Marriage': 'Date of Marriage'
        }
        
        # Final column names for the output DataFrame
        self.final_column_mapping = {
            'First Name': 'First name',
            'Last Name': 'Last name',
            "Father's Name / Husband'sName": 'Father/Husband name',
            'Sex': 'Sex',
            'Date of Birth': 'DoB',
            'CNIC #': 'CNIC',
            'CNIC Expiry Date': 'CNIC Expiry',
            'Mobile #': 'Mobile',
            'Email': 'Email',
            'Blood Group': 'Blood Gorup',
            'Marital Status': 'Martial Status',
            'Date of Marriage': 'DoM',
            'No Of Dependents': 'No. of Dependendts'
        }
        
        # Default values for missing data
        self.fill_defaults = {
            'Sex': 'N/A', 'Email': 'N/A', 'Blood Gorup': 'N/A', 'Martial Status': 'N/A',
            'Mobile': '0000000000', 'CNIC': '0000000000000', 'First name': 'N/A',
            'Last name': 'N/A', 'Father/Husband name': 'N/A', 'DoB': '1900-01-01',
            'DoM': '1900-01-01', 'CNIC Expiry': '1900-01-01', 'No. of Dependendts': 0
        }
    
    def _setup_logger(self) -> logging.Logger:
        # This method is good, no changes needed.
        logger = logging.getLogger('PersonDataPipeline')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    # --- REMOVED ---
    # The load_data method has been removed. The FastAPI router now handles
    # reading the file into a DataFrame, which is then passed to this pipeline.
    # def load_data(self, file_path: str, ...):
    #     ...

    # --- All internal helper methods are excellent and require no changes ---
    # They are already designed to operate on a DataFrame or its rows/values.
    def extract_person_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # ... (code is good)
        try:
            available_columns = [col for col in self.column_mapping.keys() if col in df.columns]
            if not available_columns:
                raise ValueError("No matching person columns found in the data")
            person_data = df[available_columns].copy()
            self.logger.info(f"Extracted {len(available_columns)} person columns")
            return person_data
        except Exception as e:
            self.logger.error(f"Error extracting person columns: {str(e)}")
            raise

    def split_name(self, name):
        # ... (code is good)
        if pd.isnull(name):
            return pd.Series({'First Name': None, 'Last Name': None})
        parts = str(name).strip().split()
        if len(parts) == 0:
            return pd.Series({'First Name': None, 'Last Name': None})
        elif len(parts) == 1:
            return pd.Series({'First Name': parts[0], 'Last Name': 'N/A'})
        else:
            return pd.Series({'First Name': ' '.join(parts[:-1]), 'Last Name': parts[-1]})
            
    # ... all other cleaning methods (clean_email, process_dates, etc.) are also fine ...
    def clean_email(self, email: str) -> str:
        if pd.isnull(email): return None
        parts = [e.strip().lower() for e in re.split(r'[;,/]', str(email)) if e.strip()]
        return ', '.join(parts) if parts else None

    def clean_date(self, date_str: str) -> str:
        if pd.isnull(date_str): return None
        try:
            dt = pd.to_datetime(str(date_str), errors='coerce', dayfirst=True)
            return dt.strftime('%Y-%m-%d') if not pd.isnull(dt) else None
        except Exception: return None

    def process_names(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'Employee Name' in df.columns:
            name_splits = df['Employee Name'].apply(self.split_name)
            df[['First Name', 'Last Name']] = name_splits
            df = df.drop(columns=['Employee Name'])
            self.logger.info("Successfully split employee names")
        return df

    def process_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'Email' in df.columns:
            df['Email'] = df['Email'].apply(self.clean_email)
        return df

    def process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        date_columns = ['Date of Birth', 'Date of Marriage', 'CNIC Expiry Date']
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.clean_date)
        return df

    def process_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'No Of Dependents' in df.columns:
            df['No Of Dependents'] = pd.to_numeric(df['No Of Dependents'], errors='coerce').fillna(0).astype(int)
        return df

    def reorder_and_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.rename(columns=self.final_column_mapping)
        return df

    def fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.fillna(value=self.fill_defaults)
        return df

    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        # ... (code is good)
        return {} # Placeholder for brevity

    # --- REFACTORED: The main process_pipeline method ---
    def process_pipeline(self, data_frame: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs the complete data cleaning pipeline on a provided DataFrame.
        
        Args:
            data_frame: The raw DataFrame to be processed.
            
        Returns:
            A dictionary with the processed DataFrame, validation report, and success status.
        """
        try:
            self.logger.info("Starting person data cleaning pipeline on provided DataFrame.")
            
            # The DataFrame is now passed in directly.
            df = data_frame
            
            df = self.extract_person_columns(df)
            df = self.process_names(df)
            df = self.process_emails(df)
            df = self.process_dates(df)
            df = self.process_numeric_columns(df)
            df = self.reorder_and_rename_columns(df)
            df = self.fill_missing_values(df)
            validation_report = self.validate_data(df)
            
            self.logger.info("Person data cleaning pipeline completed successfully.")
            
            return {
                'cleaned_data': df,
                'validation_report': validation_report,
                'success': True,
                'message': 'Pipeline completed successfully'
            }
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True) # exc_info provides full traceback
            return {
                'cleaned_data': None,
                'validation_report': None,
                'success': False,
                'message': error_msg
            }