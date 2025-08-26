import pandas as pd
import re
from typing import Dict, Any, List, Optional
import logging

class DesignationDataPipeline:
    """A class to extract and clean designation data from a pandas DataFrame."""
    
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
    
    # --- REMOVED ---
    # The load_data method is removed. The FastAPI router is responsible for loading
    # the initial DataFrame from the uploaded file.
    # def load_data(self, file_path: str, ...):
    #     ...

    def extract_designation_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only the designation-related columns from the DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with only designation columns
        """
        try:
            available_columns = [col for col in self.column_mapping.keys() if col in df.columns]
            
            if not available_columns:
                self.logger.warning("No matching designation columns found in the data")
                # Return an empty but correctly-structured DataFrame
                return pd.DataFrame(columns=list(self.column_mapping.values()))
            
            designation_data = df[available_columns].copy()
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
            # Replace missing values with a consistent 'Unknown' string
            # This is better than NaN for string operations
            df[col] = df[col].fillna('Unknown')
            
            # Chain string operations for efficiency
            df[col] = (df[col].astype(str)
                               .str.strip()
                               .str.title()
                               .replace(['', 'Nan', 'None', 'N/A', 'Na'], 'Unknown', regex=False))
        
        self.logger.info("Cleaned designation values")
        return df
    
    # --- REFACTORED: The main process_pipeline method ---
    def process_pipeline(self, data_frame: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs the complete designation data cleaning pipeline on a DataFrame.
        
        Args:
            data_frame: The raw DataFrame to be processed.
            
        Returns:
            Dictionary with the processed DataFrame and success status.
        """
        try:
            self.logger.info("Starting designation data cleaning pipeline on provided DataFrame.")
            
            # The DataFrame is passed in directly, not loaded from a file.
            df = data_frame
            
            # Step 1: Extract designation columns
            df = self.extract_designation_columns(df)
            
            # Step 2: Clean designations
            df = self.clean_designations(df)
            
            self.logger.info("Designation data cleaning pipeline completed successfully.")
            
            return {
                'cleaned_data': df,
                'success': True,
                'message': 'Pipeline completed successfully'
            }
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'cleaned_data': None,
                'success': False,
                'message': error_msg
            }