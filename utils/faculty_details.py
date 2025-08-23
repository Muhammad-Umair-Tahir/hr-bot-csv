import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

class FacultyDataPipeline:
    """
    A comprehensive data cleaning pipeline for faculty/employee details files.
    Processes raw Excel/CSV data and prepares it for database insertion or analysis.
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
        logger = logging.getLogger('FacultyDataPipeline')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def load_data(self, file_path: str, max_rows: Optional[int] = None) -> pd.DataFrame:
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

    def extract_faculty_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        available_columns = [col for col in self.column_mapping.keys() if col in df.columns]
        if not available_columns:
            raise ValueError("No matching faculty columns found in the data")
        faculty_data = df[available_columns].copy()
        self.logger.info(f"Extracted {len(available_columns)} faculty columns")
        return faculty_data

    def process_code_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert the 'Code' column to int for DB compatibility (Faculty.code is Integer).
        """
        if 'Code' in df.columns:
            def to_int(x):
                try:
                    if pd.isna(x) or x == 'N/A' or x == '':
                        return None
                    return int(float(x))
                except Exception:
                    return None
            df['Code'] = df['Code'].apply(to_int)
            self.logger.info("Converted 'Code' column to int.")
        return df

    def clean_email(self, email: str) -> str:
        if pd.isnull(email):
            return None
        parts = [e.strip().lower() for e in re.split(r'[;,/]', str(email)) if e.strip()]
        return ', '.join(parts) if parts else None

    def clean_date(self, date_str: str) -> str:
        if pd.isnull(date_str):
            return None
        try:
            # Try to parse with explicit format first
            dt = pd.to_datetime(str(date_str), format='%Y-%m-%d', errors='coerce')
            if pd.isnull(dt):
                # Fallback to generic parsing with dayfirst True
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
        validation_report = {
            'total_rows': len(df),
            'missing_values': df.isnull().sum().to_dict(),
            'empty_strings': {},
            'issues': []
        }
        # Check for empty strings in critical fields
        critical_fields = ['Title', 'Academic Designation', 'Code']
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
            for field in critical_fields:
                if field in df.columns and (pd.isnull(row[field]) or row[field] == '' or row[field] == 'N/A'):
                    issues.append(f"Missing {field}")
            if issues:
                problematic_rows.append({'row': idx + 1, 'issues': issues})
        validation_report['problematic_rows'] = problematic_rows
        validation_report['is_valid'] = len(problematic_rows) == 0
        self.logger.info(f"Validation complete. Found {len(problematic_rows)} problematic rows")
        return validation_report

    def print_stats(self, df: pd.DataFrame):
        print("=== BASIC FILE INFO ===")
        print(f"Total rows: {df.shape[0]}")
        print(f"Total columns: {df.shape[1]}")
        print(f"Column names: {list(df.columns)}")
        print("\n=== DATA COMPLETENESS ANALYSIS ===")
        rows_with_any_data = df.dropna(how='all').shape[0]
        completely_empty_rows = df.shape[0] - rows_with_any_data
        rows_with_complete_data = df.dropna().shape[0]
        rows_with_missing_data = df.isnull().any(axis=1).sum()
        print(f"Rows with at least some data: {rows_with_any_data}")
        print(f"Completely empty rows: {completely_empty_rows}")
        print(f"Rows with complete data (no missing values): {rows_with_complete_data}")
        print(f"Rows with any missing values: {rows_with_missing_data}")
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.count().sum()
        completeness_percentage = (non_null_cells / total_cells) * 100 if total_cells else 0
        print(f"\nData completeness: {completeness_percentage:.2f}%")
        print(f"Total cells: {total_cells:,}")
        print(f"Filled cells: {non_null_cells:,}")
        print(f"Empty cells: {(total_cells - non_null_cells):,}")
        print("\n=== MISSING VALUES PER COLUMN ===")
        missing_per_column = df.isnull().sum()
        missing_percentage = (missing_per_column / len(df)) * 100 if len(df) else 0
        for col in df.columns:
            missing_count = missing_per_column[col]
            missing_pct = missing_percentage[col] if isinstance(missing_percentage, pd.Series) else 0
            filled_count = len(df) - missing_count
            print(f"{col}: {filled_count}/{len(df)} filled ({100-missing_pct:.1f}%) | {missing_count} missing ({missing_pct:.1f}%)")
        print("\n=== DATA DISTRIBUTION BY ROW ===")
        non_null_per_row = df.count(axis=1)
        print(f"Rows with all {df.shape[1]} fields filled: {(non_null_per_row == df.shape[1]).sum()}")
        print(f"Rows with 0 fields filled: {(non_null_per_row == 0).sum()}")
        print("\nDistribution of filled fields per row:")
        distribution = non_null_per_row.value_counts().sort_index()
        for fields_count, row_count in distribution.items():
            percentage = (row_count / len(df)) * 100 if len(df) else 0
            print(f"  {fields_count} fields: {row_count} rows ({percentage:.1f}%)")
        print("\n=== SUMMARY ===")
        print(f"✅ Usable rows (with some data): {rows_with_any_data:,}")
        print(f"🔍 Rows needing attention (missing some data): {rows_with_missing_data - completely_empty_rows:,}")
        print(f"❌ Empty rows to remove: {completely_empty_rows:,}")
        print(f"🎯 Perfect rows (complete data): {rows_with_complete_data:,}")

    def process_pipeline(self, file_path: str, output_path: Optional[str] = None, max_rows: Optional[int] = None) -> Dict[str, Any]:
        try:
            self.logger.info(f"Starting faculty data cleaning pipeline for {file_path}")
            df = self.load_data(file_path, max_rows)
            self.print_stats(df)
            df = self.extract_faculty_columns(df)
            df = self.process_emails(df)
            df = self.process_dates(df)
            df = self.process_code_column(df)
            df = self.fill_missing_values(df)
            # Fill missing 'Title' and 'Academic Designation' with 'Unknown' before validation
            for col in ['Title', 'Academic Designation']:
                if col in df.columns:
                    df[col] = df[col].replace(['', 'N/A', None], 'Unknown').fillna('Unknown')
            validation_report = self.validate_data(df)
            if output_path:
                df.to_csv(output_path, index=False)
                self.logger.info(f"Cleaned data saved to {output_path}")
            self.logger.info("Faculty data cleaning pipeline completed successfully")
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
