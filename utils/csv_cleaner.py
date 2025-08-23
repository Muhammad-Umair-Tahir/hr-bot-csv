import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

class PersonDataPipeline:
    """
    A comprehensive data cleaning pipeline for person details CSV files.
    Processes raw CSV data and prepares it for database insertion.
    """
    
    def __init__(self):
        self.logger = self._setup_logger()
        
        # Column mapping configuration
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
        
        # Final column names for database
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
            'Sex': 'N/A',
            'Email': 'N/A',
            'Blood Gorup': 'N/A',
            'Martial Status': 'N/A',
            'Mobile': '0000000000',
            'CNIC': '0000000000000',
            'First name': 'N/A',
            'Last name': 'N/A',
            'Father/Husband name': 'N/A',
            'DoB': '1900-01-01',
            'DoM': '1900-01-01',
            'CNIC Expiry': '1900-01-01',
            'No. of Dependendts': 0
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the pipeline."""
        logger = logging.getLogger('PersonDataPipeline')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_data(self, file_path: str, max_rows: Optional[int] = None) -> pd.DataFrame:
        """
        Load data from Excel or CSV file.
        
        Args:
            file_path: Path to the input file
            max_rows: Maximum number of rows to process (optional)
            
        Returns:
            pandas DataFrame with loaded data
        """
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                data = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                data = pd.read_csv(file_path)
            else:
                raise ValueError("Unsupported file format. Use .xlsx, .xls, or .csv")
            
            if max_rows:
                data = data.iloc[:max_rows]
            
            self.logger.info(f"Loaded {len(data)} rows from {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise
    
    def extract_person_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only the person-related columns from the DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with only person columns
        """
        try:
            # Get available columns that match our mapping
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
        """
        Split employee name into first and last name.
        
        Args:
            name: Full name string
            
        Returns:
            Series with First Name and Last Name
        """
        if pd.isnull(name):
            return pd.Series({'First Name': None, 'Last Name': None})
        
        name = str(name).strip()  # Convert to string to handle any data type
        parts = name.split()
        
        # Handle empty or no parts
        if len(parts) == 0:
            return pd.Series({'First Name': None, 'Last Name': None})
        # If only one word, set it as first name and use 'N/A' for last name
        elif len(parts) == 1:
            return pd.Series({'First Name': parts[0], 'Last Name': 'N/A'})
        # If only two words, split directly
        elif len(parts) == 2:
            return pd.Series({'First Name': parts[0], 'Last Name': parts[1]})
        # If more than two, handle initials and multi-part first names
        else:
            first_name_parts = []
            last_name_parts = []
            for i, part in enumerate(parts):
                # Initials or single-letter with dot
                if re.match(r'^[A-Z]\.$', part) or (i == 0 and len(part) == 1):
                    first_name_parts.append(part)
                elif i == 0 and len(part) > 1 and part.endswith('.'):
                    first_name_parts.append(part)
                elif len(first_name_parts) == 0:
                    first_name_parts.append(part)
                else:
                    # Once we have at least two words in first name, rest is last name
                    if len(first_name_parts) < 2:
                        first_name_parts.append(part)
                    else:
                        last_name_parts = parts[i:]
                        break
        
        if not last_name_parts:
            # fallback: last word as last name, rest as first name
            if len(parts) > 1:
                return pd.Series({
                    'First Name': ' '.join(parts[:-1]), 
                    'Last Name': parts[-1]
                })
            else:
                return pd.Series({
                    'First Name': parts[0], 
                    'Last Name': 'N/A'
                })
        
        return pd.Series({
            'First Name': ' '.join(first_name_parts), 
            'Last Name': ' '.join(last_name_parts)
        })
    
    def clean_email(self, email: str) -> str:
        """
        Clean email addresses by removing extra spaces and separators.
        
        Args:
            email: Email string
            
        Returns:
            Cleaned email string
        """
        if pd.isnull(email):
            return None
        
        # Split by common separators, strip spaces, remove empty, join with comma
        parts = [e.strip().lower() for e in re.split(r'[;,/]', str(email)) if e.strip()]
        return ', '.join(parts) if parts else None
    
    def clean_date(self, date_str: str) -> str:
        """
        Clean and standardize date format.
        
        Args:
            date_str: Date string
            
        Returns:
            Standardized date string (YYYY-MM-DD)
        """
        if pd.isnull(date_str):
            return None
        
        try:
            dt = pd.to_datetime(str(date_str), errors='coerce', dayfirst=True)
            if pd.isnull(dt):
                return None
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return None
    
    def process_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process employee names by splitting into first and last names.
        
        Args:
            df: DataFrame with Employee Name column
            
        Returns:
            DataFrame with First Name and Last Name columns
        """
        if 'Employee Name' in df.columns:
            name_splits = df['Employee Name'].apply(self.split_name)
            df[['First Name', 'Last Name']] = name_splits
            df = df.drop(columns=['Employee Name'])
            self.logger.info("Successfully split employee names")
        else:
            self.logger.warning("Employee Name column not found")
        
        return df
    
    def process_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean email addresses.
        
        Args:
            df: DataFrame with Email column
            
        Returns:
            DataFrame with cleaned emails
        """
        if 'Email' in df.columns:
            df['Email'] = df['Email'].apply(self.clean_email)
            self.logger.info("Successfully cleaned email addresses")
        
        return df
    
    def process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize date columns.
        
        Args:
            df: DataFrame with date columns
            
        Returns:
            DataFrame with cleaned dates
        """
        date_columns = ['Date of Birth', 'Date of Marriage', 'CNIC Expiry Date']
        
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.clean_date)
                self.logger.info(f"Cleaned {col} column")
        
        return df
    
    def process_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process numeric columns.
        
        Args:
            df: DataFrame with numeric columns
            
        Returns:
            DataFrame with processed numeric columns
        """
        if 'No Of Dependents' in df.columns:
            df['No Of Dependents'] = df['No Of Dependents'].fillna(0).astype(int)
            self.logger.info("Processed No Of Dependents column")
        
        return df
    
    def reorder_and_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reorder and rename columns to match database schema.
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with reordered and renamed columns
        """
        # Define the desired column order
        ordered_columns = [
            'First Name', 'Last Name', "Father's Name / Husband'sName", 'Sex', 'Email', 'CNIC #', 'CNIC Expiry Date',
            'Date of Birth', 'Mobile #', 'Blood Group', 'Marital Status', 'No Of Dependents', 'Date of Marriage'
        ]
        
        # Reorder columns
        df = df[[col for col in ordered_columns if col in df.columns]]
        
        # Rename columns
        df = df.rename(columns=self.final_column_mapping)
        
        # Define the required final order
        final_order = [
            'First name', 'Last name', 'Father/Husband name', 'Sex', 'DoB',
            'CNIC', 'CNIC Expiry', 'Mobile', 'Email', 'Blood Gorup',
            'Martial Status', 'DoM', 'No. of Dependendts'
        ]
        
        # Reorder to final order
        df = df[[col for col in final_order if col in df.columns]]
        
        self.logger.info("Successfully reordered and renamed columns")
        return df
    
    def fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill missing values with default values.
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with filled missing values
        """
        # First fill with our default values
        df = df.fillna(value=self.fill_defaults)
        
        # Handle specific cases for names after filling defaults
        # If Last name is still None or 'N/A' but First name exists, use 'Unknown'
        mask = (df['Last name'].isin([None, 'N/A', '']) | df['Last name'].isnull()) & \
               (df['First name'].notna() & ~df['First name'].isin(['N/A', '']))
        df.loc[mask, 'Last name'] = 'Unknown'
        
        # If First name is None or 'N/A' but Last name exists, use 'Unknown'
        mask = (df['First name'].isin([None, 'N/A', '']) | df['First name'].isnull()) & \
               (df['Last name'].notna() & ~df['Last name'].isin(['N/A', '']))
        df.loc[mask, 'First name'] = 'Unknown'
        
        self.logger.info("Successfully filled missing values with defaults")
        return df
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the cleaned data and return validation report.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_report = {
            'total_rows': len(df),
            'missing_values': df.isnull().sum().to_dict(),
            'empty_strings': {},
            'issues': []
        }
        
        # Check for empty strings in critical fields
        critical_fields = ['First name', 'Last name', 'Sex']
        
        for field in critical_fields:
            if field in df.columns:
                empty_count = (df[field] == '').sum()
                validation_report['empty_strings'][field] = empty_count
                
                if empty_count > 0:
                    validation_report['issues'].append(f"{field} has {empty_count} empty values")
        
        # Check for problematic rows
        problematic_rows = []
        for idx, row in df.iterrows():
            issues = []
            
            # Check for missing critical fields
            for field in critical_fields:
                if field in df.columns and (pd.isnull(row[field]) or row[field] == '' or row[field] == 'N/A'):
                    issues.append(f"Missing {field}")
            
            if issues:
                problematic_rows.append({'row': idx + 1, 'issues': issues})
        
        validation_report['problematic_rows'] = problematic_rows
        validation_report['is_valid'] = len(problematic_rows) == 0
        
        self.logger.info(f"Validation complete. Found {len(problematic_rows)} problematic rows")
        return validation_report
    
    def process_pipeline(self, file_path: str, output_path: Optional[str] = None, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the complete data cleaning pipeline.
        
        Args:
            file_path: Path to input file
            output_path: Path to save cleaned CSV (optional)
            max_rows: Maximum number of rows to process (optional)
            
        Returns:
            Dictionary with processed DataFrame and validation report
        """
        try:
            self.logger.info(f"Starting data cleaning pipeline for {file_path}")
            
            # Step 1: Load data
            df = self.load_data(file_path, max_rows)
            
            # Step 2: Extract person columns
            df = self.extract_person_columns(df)
            
            # Step 3: Process names
            df = self.process_names(df)
            
            # Step 4: Process emails
            df = self.process_emails(df)
            
            # Step 5: Process dates
            df = self.process_dates(df)
            
            # Step 6: Process numeric columns
            df = self.process_numeric_columns(df)
            
            # Step 7: Reorder and rename columns
            df = self.reorder_and_rename_columns(df)
            
            # Step 8: Fill missing values
            df = self.fill_missing_values(df)
            
            # Step 9: Validate data
            validation_report = self.validate_data(df)
            
            # Step 10: Save cleaned data if output path provided
            if output_path:
                df.to_csv(output_path, index=False)
                self.logger.info(f"Cleaned data saved to {output_path}")
            
            self.logger.info("Data cleaning pipeline completed successfully")
            
            return {
                'cleaned_data': df,
                'validation_report': validation_report,
                'success': True,
                'message': 'Pipeline completed successfully'
            }
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'cleaned_data': None,
                'validation_report': None,
                'success': False,
                'message': error_msg
            }
