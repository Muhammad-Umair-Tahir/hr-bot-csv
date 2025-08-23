import pandas as pd
import re
from typing import Dict, Any, List, Optional
import logging

class QualificationDataPipeline:
    """A class to extract qualification data from CSV files"""
    
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
    
    def extract_qualifications(self, row: pd.Series, person_id: int) -> List[Dict[str, Any]]:
        """
        Extract qualifications from a CSV row.
        Looks for columns that might contain degree information.
        
        Args:
            row: A pandas Series representing a row from the CSV
            person_id: The ID of the person to associate qualifications with
            
        Returns:
            A list of dictionaries containing qualification data
        """
        qualifications = []
        
        # Look for qualification columns in the row
        # Common patterns: "Degree", "Qualification", "Education", etc.
        degree_columns = [col for col in row.index if any(term in col.lower() for term in 
                                                       ["degree", "qualification", "education"])]
        
        if not degree_columns:
            self.logger.warning("No qualification columns found in the data")
            return qualifications
        
        # For each identified column, extract qualification details
        for col in degree_columns:
            value = row[col]
            
            # Skip empty values
            if pd.isna(value) or value == "" or value == "N/A":
                continue
            
            # Basic extraction - in real application, this would be more sophisticated
            qualification = {
                "person_id": person_id,
                "degree": value,
                "field_of_study": self._extract_field(value, row),
                "institution": self._extract_institution(row),
                "country": self._extract_country(row),
                "year_completed": self._extract_year(row)
            }
            
            qualifications.append(qualification)
            self.logger.info(f"Extracted qualification: {qualification['degree']}")
        
        return qualifications
    
    def _extract_field(self, degree_value: str, row: pd.Series) -> Optional[str]:
        """Extract field of study from the degree value or other columns"""
        # Look for field columns
        field_columns = [col for col in row.index if any(term in col.lower() for term in 
                                                     ["field", "major", "subject", "specialization"])]
        
        if field_columns:
            # Use the first non-empty field column
            for col in field_columns:
                if not pd.isna(row[col]) and row[col] != "" and row[col] != "N/A":
                    return row[col]
        
        # Try to extract from degree value
        # This is a simplified approach
        parts = str(degree_value).split(" in ")
        if len(parts) > 1:
            return parts[1]
        
        return None
    
    def _extract_institution(self, row: pd.Series) -> Optional[str]:
        """Extract institution name from columns"""
        institution_columns = [col for col in row.index if any(term in col.lower() for term in 
                                                           ["institution", "university", "college", "school"])]
        
        if institution_columns:
            # Use the first non-empty institution column
            for col in institution_columns:
                if not pd.isna(row[col]) and row[col] != "" and row[col] != "N/A":
                    return row[col]
        
        return None
    
    def _extract_country(self, row: pd.Series) -> Optional[str]:
        """Extract country from columns"""
        country_columns = [col for col in row.index if any(term in col.lower() for term in 
                                                       ["country", "nation"])]
        
        if country_columns:
            # Use the first non-empty country column
            for col in country_columns:
                if not pd.isna(row[col]) and row[col] != "" and row[col] != "N/A":
                    return row[col]
        
        return None
    
    def _extract_year(self, row: pd.Series) -> Optional[int]:
        """Extract year from columns"""
        year_columns = [col for col in row.index if any(term in col.lower() for term in 
                                                    ["year", "date", "completion", "graduation"])]
        
        if year_columns:
            # Use the first non-empty year column
            for col in year_columns:
                if not pd.isna(row[col]) and row[col] != "" and row[col] != "N/A":
                    # Try to extract a 4-digit year
                    matches = re.findall(r'(19|20)\d{2}', str(row[col]))
                    if matches:
                        return int(matches[0])
        
        return None
    
    def process_pipeline(self, file_path: str) -> Dict[str, Any]:
        """
        Process the qualification pipeline.
        This is a placeholder that would be implemented for standalone usage.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dictionary with pipeline results
        """
        self.logger.info(f"Qualification pipeline would process {file_path}")
        return {
            "message": "Qualification pipeline is designed to be used with the CSV upload endpoint, not standalone."
        }
