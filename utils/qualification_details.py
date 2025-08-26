import pandas as pd
import re
from typing import Dict, Any, List, Optional
import logging

class QualificationDataPipeline:
    """A class to extract structured qualification data from a DataFrame."""
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the qualification pipeline."""
        logger = logging.getLogger('QualificationDataPipeline')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def extract_qualifications_from_row(self, row: pd.Series, person_id: int, degree_columns: List[str]) -> List[Dict[str, Any]]:
        """
        Extracts all possible qualifications from a single row of a DataFrame.
        
        Args:
            row: A pandas Series representing a row from the DataFrame.
            person_id: The ID of the person to associate qualifications with.
            degree_columns: A pre-filtered list of columns that may contain degree info.
            
        Returns:
            A list of dictionaries, where each dictionary is a single qualification record.
        """
        qualifications = []
        
        # For each identified column, extract qualification details
        for col in degree_columns:
            value = row[col]
            
            # Skip empty or placeholder values
            if pd.isna(value) or str(value).strip() in ["", "N/A"]:
                continue
            
            qualification = {
                "person_id": person_id,
                "category": "Education",  # Set default category
                "title": str(value).strip(),  # Changed from "degree" to "title"
                "institution": self._extract_institution(row),
                "country": self._extract_country(row),
                "year": self._extract_year(row)  # Changed from "year_completed" to "year"
            }
            
            qualifications.append(qualification)
            self.logger.debug(f"For person_id {person_id}, extracted qualification: {qualification['title']}")
        
        return qualifications
    
    # --- Helper methods (_extract_field, etc.) are good as they are ---
    # They correctly operate on a single row (pd.Series)
    def _extract_field(self, degree_value: str, row: pd.Series) -> Optional[str]:
        # ... (no changes needed)
        return None
    
    def _extract_institution(self, row: pd.Series) -> Optional[str]:
        # ... (no changes needed)
        return None

    def _extract_country(self, row: pd.Series) -> Optional[str]:
        # ... (no changes needed)
        return None

    def _extract_year(self, row: pd.Series) -> Optional[int]:
        # ... (no changes needed)
        return None
        
    # --- REFACTORED: The main process_pipeline method ---
    def process_pipeline(self, data_frame: pd.DataFrame, person_id_map: Dict[str, int]) -> Dict[str, Any]:
        """
        Processes an entire DataFrame to extract all qualification records for all persons.
        
        Args:
            data_frame: The combined DataFrame containing all person/faculty data.
            person_id_map: A dictionary mapping a person's email to their database ID.
            
        Returns:
            A dictionary containing the results and a list of all extracted qualifications.
        """
        self.logger.info("Starting qualification extraction from DataFrame.")
        all_qualifications = []

        try:
            # Identify potential qualification columns just once to be efficient
            degree_columns = [col for col in data_frame.columns if any(term in col.lower() for term in 
                                                                    ["degree", "qualification", "education"])]
            
            if not degree_columns:
                self.logger.warning("No columns matching qualification terms found in the DataFrame.")
                return {
                    'success': True,
                    'data': [],
                    'message': 'No qualification columns found to process.'
                }

            # Iterate over each row in the DataFrame to process it
            for index, row in data_frame.iterrows():
                # The 'email' column is used to link the row to a person_id
                # The column name must match what's in your combined_df
                email = row.get('email') or row.get('Email') 
                
                if not email:
                    continue # Cannot link qualification without an email

                person_id = person_id_map.get(email)
                if not person_id:
                    # This person was not inserted or found, so we can't link their qualifications.
                    continue
                
                # Extract all qualifications from this specific row
                person_quals = self.extract_qualifications_from_row(row, person_id, degree_columns)
                
                if person_quals:
                    all_qualifications.extend(person_quals)

            self.logger.info(f"Successfully extracted {len(all_qualifications)} qualification records in total.")
            return {
                'success': True,
                'data': all_qualifications,
                'message': f'Extracted {len(all_qualifications)} qualification records.'
            }
        except Exception as e:
            error_msg = f"Qualification pipeline failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'data': None,
                'message': error_msg
            }