import pandas as pd
import re
from typing import Dict, Any, List, Optional
import logging

class DesignationDataPipeline:
    """A class to extract designation data from CSV files"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
        # Column mapping configuration
        self.column_mapping = {
            'Academic Designation': 'academic_designation',
            'Administrative Designation': 'administrative_designation',
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the designation pipeline."""
        logger = logging.getLogger('DesignationDataPipeline')
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
    
    def extract_designation_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only the designation-related columns from the DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with only designation columns
        """
        try:
            # Get available columns that match our mapping
            available_columns = [col for col in self.column_mapping.keys() if col in df.columns]
            
            if not available_columns:
                # Create empty dataframe with expected columns if none found
                self.logger.warning("No matching designation columns found in the data")
                return pd.DataFrame(columns=list(self.column_mapping.values()))
            
            designation_data = df[available_columns].copy()
            # Rename columns according to our mapping
            designation_data = designation_data.rename(columns=self.column_mapping)
            
            self.logger.info(f"Extracted {len(available_columns)} designation columns")
            return designation_data
            
        except Exception as e:
            self.logger.error(f"Error extracting designation columns: {str(e)}")
            raise
    
    def clean_designations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean designation values.
        
        Args:
            df: DataFrame with designation columns
            
        Returns:
            DataFrame with cleaned designations
        """
        for col in df.columns:
            # Replace missing values with 'Unknown'
            df[col] = df[col].fillna('Unknown')
            
            # Clean up values - convert to string, strip whitespace, standardize casing
            df[col] = df[col].astype(str).str.strip().str.title()
            
            # Replace 'Nan', 'None', empty strings, etc. with 'Unknown'
            df[col] = df[col].replace(['', 'Nan', 'None', 'N/A', 'Na', 'Unknown'], 'Unknown')
        
        self.logger.info("Cleaned designation values")
        return df
    
    def process_pipeline(self, file_path: str, output_path: Optional[str] = None, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the complete designation data cleaning pipeline.
        
        Args:
            file_path: Path to input file
            output_path: Path to save cleaned CSV (optional)
            max_rows: Maximum number of rows to process (optional)
            
        Returns:
            Dictionary with processed DataFrame and success status
        """
        try:
            self.logger.info(f"Starting designation data cleaning pipeline for {file_path}")
            
            # Step 1: Load data
            df = self.load_data(file_path, max_rows)
            
            # Step 2: Extract designation columns
            df = self.extract_designation_columns(df)
            
            # Step 3: Clean designations
            df = self.clean_designations(df)
            
            # Step 4: Save cleaned data if output path provided
            if output_path:
                df.to_csv(output_path, index=False)
                self.logger.info(f"Cleaned designation data saved to {output_path}")
            
            self.logger.info("Designation data cleaning pipeline completed successfully")
            
            return {
                'cleaned_data': df,
                'success': True,
                'message': 'Pipeline completed successfully'
            }
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'cleaned_data': None,
                'success': False,
                'message': error_msg
            }
