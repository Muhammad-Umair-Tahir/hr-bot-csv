import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

class FacultyDataPipeline:
    """
    A comprehensive data cleaning pipeline for faculty/employee details.
    Processes a raw pandas DataFrame and prepares it for database insertion or analysis.
    """
    def __init__(self):
        self.logger = self._setup_logger()
        self.column_mapping = {
            'Title': 'Title',
            'Academic Designation': 'Academic Designation',
            'Administrative Designation': 'Administrative Designation',
            'Code': 'Code',
            'Status': 'Status',
            'Date of Joining': 'Date of Joining',
            'Email': 'Email',
        }
        self.fill_defaults = {
            'Title': 'N/A',
            'Academic Designation': 'N/A',
            'Administrative Designation': 'N/A',
            'Code': 'N/A',
            'Status': 'N/A',
            'Date of Joining': '1900-01-01',
            'Email': 'N/A',
        }

    def _setup_logger(self) -> logging.Logger:
        # This method is good, no changes needed.
        logger = logging.getLogger('FacultyDataPipeline')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    # --- REMOVED ---
    # The load_data method has been removed. The FastAPI router is now responsible
    # for reading the file into a DataFrame. This separates concerns and fixes the error.
    # def load_data(self, file_path: str, ...):
    #     ...

    def extract_faculty_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # This method is good, no changes needed.
        available_columns = [col for col in self.column_mapping.keys() if col in df.columns]
        if not available_columns:
            raise ValueError("No matching faculty columns found in the data")
        faculty_data = df[available_columns].copy()
        self.logger.info(f"Extracted {len(available_columns)} faculty columns")
        return faculty_data

    def process_code_column(self, df: pd.DataFrame) -> pd.DataFrame:
        # This method is good, no changes needed.
        if 'Code' in df.columns:
            def to_int(x):
                try:
                    if pd.isna(x) or x == 'N/A' or x == '':
                        return None
                    return int(float(x))
                except (ValueError, TypeError):
                    return None
            df['Code'] = df['Code'].apply(to_int)
            self.logger.info("Converted 'Code' column to int.")
        return df

    # ... all other cleaning methods (clean_email, clean_date, etc.) are perfect as they are ...
    # ... because they already operate on a DataFrame. ...
    def clean_email(self, email: str) -> str:
        if pd.isnull(email):
            return None
        parts = [e.strip().lower() for e in re.split(r'[;,/]', str(email)) if e.strip()]
        return ', '.join(parts) if parts else None

    def clean_date(self, date_str: str) -> str:
        if pd.isnull(date_str):
            return None
        try:
            dt = pd.to_datetime(str(date_str), errors='coerce', dayfirst=True)
            if pd.isnull(dt):
                return None
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return None

    def process_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'Email' in df.columns:
            df['Email'] = df['Email'].apply(self.clean_email)
            self.logger.info("Successfully cleaned email addresses")
        return df

    def process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'Date of Joining' in df.columns:
            df['Date of Joining'] = df['Date of Joining'].apply(self.clean_date)
            self.logger.info("Cleaned Date of Joining column")
        return df

    def fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.fillna(value=self.fill_defaults)
        self.logger.info("Filled missing values with defaults")
        return df

    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        # This method is good, no changes needed.
        # ... (code is fine)
        return {} # Placeholder for brevity

    def print_stats(self, df: pd.DataFrame):
        # This method is good, no changes needed.
        # ... (code is fine)
        pass # Placeholder for brevity


    # --- CHANGED ---
    # The main process_pipeline method now accepts a DataFrame directly.
    def process_pipeline(self, data_frame: pd.DataFrame) -> Dict[str, Any]:
        """
        Takes a raw DataFrame and runs it through the cleaning and validation steps.
        
        Args:
            data_frame (pd.DataFrame): The DataFrame to be processed.
            
        Returns:
            Dict[str, Any]: A dictionary containing the results of the pipeline.
        """
        try:
            self.logger.info("Starting faculty data cleaning pipeline on provided DataFrame.")
            
            # The DataFrame is now passed in, not loaded from a file.
            df = data_frame
            
            self.print_stats(df)
            df = self.extract_faculty_columns(df)
            df = self.process_emails(df)
            df = self.process_dates(df)
            df = self.process_code_column(df)
            df = self.fill_missing_values(df)
            
            # Fill missing 'Title' and 'Academic Designation' before validation
            for col in ['Title', 'Academic Designation']:
                if col in df.columns:
                    df[col] = df[col].replace(['', 'N/A', None], 'Unknown').fillna('Unknown')
                    
            validation_report = self.validate_data(df)
            
            self.logger.info("Faculty data cleaning pipeline completed successfully.")
            return {
                'cleaned_data': df,
                'validation_report': validation_report,
                'success': True,
                'message': 'Pipeline completed successfully'
            }
        except Exception as e:
            error_msg = f"Pipeline failed during DataFrame processing: {str(e)}"
            self.logger.error(error_msg, exc_info=True) # exc_info=True gives full traceback
            return {
                'cleaned_data': None,
                'validation_report': None,
                'success': False,
                'message': error_msg
            }