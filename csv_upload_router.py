import pandas as pd
import numpy as np
import asyncio
import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path
import tempfile

# FastAPI router for CSV upload
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI router instance to be imported in main.py
router = APIRouter()

try:
    from database.connect import get_async_session_maker, init_db, close_db
    from models.person_model import Person
    from models.education_model import Qualification
    from models.faculty_model import Faculty
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

class CSVToDBImporter:
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.session_maker = None
        
    async def initialize(self):
        await init_db()
        self.session_maker = get_async_session_maker()
        logger.info("Database connection initialized")
    
    async def close(self):
        await close_db()
        logger.info("Database connection closed")
    
    # --- Helper methods for data cleaning ---
    def parse_date(self, date_str: Any) -> Optional[datetime.date]:
        if pd.isna(date_str) or not str(date_str).strip(): return None
        try: return pd.to_datetime(date_str, errors='coerce').date()
        except Exception: return None
    
    def clean_string(self, value: Any) -> Optional[str]:
        if pd.isna(value) or not str(value).strip(): return None
        return str(value).strip()
    
    def clean_integer(self, value: Any) -> Optional[int]:
        if pd.isna(value): return None
        try: return int(float(value))
        except (ValueError, TypeError): return None
            
    async def process_csv_with_error_skipping(self) -> Dict[str, Any]:
        """
        Processes a CSV, skipping records that cause unique constraint violations
        by handling them on a person-by-person basis within nested transactions.
        """
        logger.info(f"Reading file: {self.csv_file_path}")
        suffix = Path(self.csv_file_path).suffix.lower()
        if suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(self.csv_file_path).replace({np.nan: None})
        else:
            df = pd.read_csv(self.csv_file_path).replace({np.nan: None})
        logger.info(f"Found {len(df)} rows in CSV file")

        # --- 1. Proactively Fetch Existing Data to Prevent Common Errors ---
        async with self.session_maker() as session:
            existing_cnics = {r[0] for r in await session.execute(select(Person._cnic))}
            existing_codes = {r[0] for r in await session.execute(select(Faculty.code))}
            # Fetch existing emails, ignoring None/empty values
            existing_emails = {r[0] for r in await session.execute(select(Faculty.university_email)) if r[0]}
        
        logger.info(f"Pre-fetched {len(existing_cnics)} CNICs, {len(existing_codes)} codes, and {len(existing_emails)} emails from DB.")

        # --- 2. Process Data Person-by-Person with Nested Transactions ---
        persons_processed = 0
        persons_skipped = 0
        
        # Group by a unique person identifier
        grouped = df.groupby('CNIC')
        
        async with self.session_maker() as session:
            # The main transaction block
            async with session.begin():
                for cnic, group in grouped:
                    main_row = group.iloc[0]
                    cnic_clean = self.clean_string(cnic)
                    code_clean = self.clean_integer(main_row.get('Code'))
                    email_clean = self.clean_string(main_row.get('University Email'))

                    # --- Proactive Skipping Logic ---
                    if not cnic_clean or cnic_clean in existing_cnics:
                        logger.warning(f"SKIPPING person with missing or existing CNIC: '{cnic_clean}'")
                        persons_skipped += 1
                        continue
                    if code_clean and code_clean in existing_codes:
                        logger.warning(f"SKIPPING person '{cnic_clean}' because Faculty Code '{code_clean}' already exists.")
                        persons_skipped += 1
                        continue
                    if email_clean and email_clean in existing_emails:
                        logger.warning(f"SKIPPING person '{cnic_clean}' because University Email '{email_clean}' already exists.")
                        persons_skipped += 1
                        continue

                    # --- Per-Person Transaction (Savepoint) ---
                    try:
                        # This creates a SAVEPOINT. If it fails, only this block is rolled back.
                        async with session.begin_nested():
                            # A. Create Person
                            person = Person(
                                first_name=self.clean_string(main_row.get('First Name')) or "Unknown",
                                last_name=self.clean_string(main_row.get('Last Name')) or "Unknown",
                                father_husband_name=self.clean_string(main_row.get('Father/Husband Name')),
                                sex=self.clean_string(main_row.get('Sex')) or "M",
                                dob=self.parse_date(main_row.get('Date of Birth')),
                                phone=self.clean_string(main_row.get('Phone Number')),
                                email=self.clean_string(main_row.get('Personal Email')),
                                blood_group=self.clean_string(main_row.get('Blood Group')),
                                marital_status=self.clean_string(main_row.get('Martial Status')),
                                date_of_marriage=self.parse_date(main_row.get('Date of Marriage')),
                                no_of_dependents=self.clean_integer(main_row.get('No Of Dependent')),
                                cnic_expiry=self.parse_date(main_row.get('CNIC Expiry'))
                            )
                            person.cnic = cnic_clean
                            session.add(person)
                            await session.flush() # Flush to get the person.id

                            # B. Create Faculty (if code exists)
                            if code_clean:
                                faculty = Faculty(
                                    code=code_clean,
                                    person_id=person.id,
                                    university_email=email_clean,
                                    title=self.clean_string(main_row.get('Faculty Title')) or "Faculty",
                                    status=self.clean_string(main_row.get('Status')) or "Active",
                                    academic_designation=self.clean_string(main_row.get('Academic Designation')),
                                    administrative_designation=self.clean_string(main_row.get('Administrative Designation')),
                                    date_of_joining=self.parse_date(main_row.get('Date of Joining')) or datetime.now().date(),
                                    teaching_experience=self.clean_integer(main_row.get('Teaching Experience')) or 0,
                                    professional_experience=self.clean_integer(main_row.get('Professional Experience')) or 0
                                )
                                session.add(faculty)
                            
                            # C. Create Qualifications
                            for _, qual_row in group.iterrows():
                                qual_title = self.clean_string(qual_row.get('Qualification Title'))
                                if qual_title:
                                    qualification = Qualification(
                                        person_id=person.id,
                                        title=qual_title,
                                        category=self.clean_string(qual_row.get('Category (Educational, Professional)')) or "Educational",
                                        institution=self.clean_string(qual_row.get('Institution')),
                                        country=self.clean_string(qual_row.get('Country')),
                                        year=self.clean_integer(qual_row.get('Year'))
                                    )
                                    session.add(qualification)
                        
                        # If the nested transaction succeeded, we count it.
                        persons_processed += 1
                        logger.info(f"Successfully processed and staged person: {cnic_clean}")

                    except IntegrityError as e:
                        # The nested transaction is automatically rolled back here.
                        logger.error(f"SKIPPING person {cnic_clean} due to a database integrity error (e.g., a duplicate not caught by pre-fetch): {e.orig}")
                        persons_skipped += 1
                    except Exception as e:
                        logger.error(f"SKIPPING person {cnic_clean} due to an unexpected error: {e}")
                        persons_skipped += 1
            
            # The main transaction is committed here, saving all successful persons.
            logger.info("Main transaction committed.")

        logger.info(f"""
        Import process finished!
        - Persons successfully processed: {persons_processed}
        - Persons skipped due to errors or duplicates: {persons_skipped}
        """)

        return {
            "processed": persons_processed,
            "skipped": persons_skipped,
            "total": persons_processed + persons_skipped,
        }

async def main():
    CSV_FILE_PATH = r"D:\Projects\OHCM-HR\cleaned_faculty_data_final.csv"
    if not os.path.exists(CSV_FILE_PATH):
        logger.error(f"CSV file not found: {CSV_FILE_PATH}")
        return
    
    importer = CSVToDBImporter(CSV_FILE_PATH)
    
    try:
        await importer.initialize()
        await importer.process_csv_with_error_skipping()
    except Exception as e:
        logger.error(f"Import process failed with an unhandled exception: {e}")
    finally:
        await importer.close()

if __name__ == "__main__":
    asyncio.run(main())


# =============================
# FastAPI Endpoints
# =============================

@router.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV/Excel file and import its contents into the database."""
    filename = file.filename or "uploaded_file"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="Only .csv, .xlsx, or .xls files are supported")

    try:
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name

        importer = CSVToDBImporter(temp_path)
        try:
            await importer.initialize()
            result = await importer.process_csv_with_error_skipping()
            return JSONResponse({
                "status": "success",
                "filename": filename,
                "summary": result,
            })
        finally:
            await importer.close()
            # Clean up temp file
            try:
                os.remove(temp_path)
            except Exception:
                pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload/import failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the uploaded file")