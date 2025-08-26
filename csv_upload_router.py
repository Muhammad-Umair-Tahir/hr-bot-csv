import os
import tempfile
import logging
from typing import Dict, Any, List

import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession

from database.connect import get_db_session
from models.designation_model import Designation, DesignationType
from models.education_model import Qualification
from models.faculty_model import Faculty
from models.person_model import Person
from schemas.schema import FacultyOut
from utils.csv_cleaner import PersonDataPipeline
from utils.faculty_details import FacultyDataPipeline
from utils.qualification_details import QualificationDataPipeline

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class CSVUploadError(Exception):
    """Custom exception for CSV upload errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def create_error_response(message: str, status_code: int = 400) -> JSONResponse:
    """Create standardized error response"""
    logger.error(f"CSV Upload Error: {message}")
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": message,
            "data": None
        }
    )


def create_success_response(data: Dict[str, Any], message: str = "Success") -> JSONResponse:
    """Create standardized success response"""
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": message,
            "data": data
        }
    )


async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file to temporary location"""
    try:
        suffix = ".xlsx" if file.filename.endswith((".xlsx", ".xls")) else ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            return tmp.name
    except Exception as e:
        raise CSVUploadError(f"Failed to save uploaded file: {str(e)}", 400)


def read_and_validate_file(file_path: str) -> pd.DataFrame:
    """Read and validate the uploaded file"""
    try:
        if file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = pd.read_csv(file_path)
        
        # Ensure column names are strings
        df.columns = [str(col) for col in df.columns]
        
        if df.empty:
            raise CSVUploadError("Uploaded file is empty", 400)
        
        logger.info(f"Successfully loaded {len(df)} rows from file")
        return df
        
    except pd.errors.EmptyDataError:
        raise CSVUploadError("File is empty or corrupted", 400)
    except pd.errors.ParserError as e:
        raise CSVUploadError(f"Failed to parse file: {str(e)}", 400)
    except Exception as e:
        raise CSVUploadError(f"Failed to read file: {str(e)}", 400)


def process_pipelines(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Process data through cleaning pipelines"""
    try:
        # Person pipeline
        person_pipeline = PersonDataPipeline()
        person_result = person_pipeline.process_pipeline(df.copy())
        if not person_result.get('success'):
            raise CSVUploadError(f"Person data processing failed: {person_result.get('message', 'Unknown error')}", 400)
        
        # Faculty pipeline
        faculty_pipeline = FacultyDataPipeline()
        faculty_result = faculty_pipeline.process_pipeline(df.copy())
        if not faculty_result.get('success'):
            raise CSVUploadError(f"Faculty data processing failed: {faculty_result.get('message', 'Unknown error')}", 400)
        
        person_df = person_result['cleaned_data']
        faculty_df = faculty_result['cleaned_data']
        
        # Validate row counts match
        if len(person_df) != len(faculty_df):
            raise CSVUploadError("Person and faculty data row count mismatch", 400)
        
        return {
            'person': person_df,
            'faculty': faculty_df
        }
        
    except CSVUploadError:
        raise
    except Exception as e:
        raise CSVUploadError(f"Data processing failed: {str(e)}", 400)


def standardize_column_names(dataframes: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Standardize column names and combine dataframes"""
    try:
        person_df = dataframes['person']
        faculty_df = dataframes['faculty']
        
        # Person column mapping
        person_columns = {
            'First name': 'first_name',
            'Last name': 'last_name',
            'Father/Husband name': 'father_husband_name',
            'Sex': 'sex',
            'DoB': 'dob',
            'CNIC': 'cnic',
            'CNIC Expiry': 'cnic_expiry',
            'Mobile': 'phone',
            'Email': 'email',
            'Blood Gorup': 'blood_group',
            'Martial Status': 'marital_status',
            'DoM': 'date_of_marriage',
            'No. of Dependendts': 'no_of_dependents'
        }
        
        # Faculty column mapping
        faculty_columns = {
            'Code': 'code',
            'Title': 'title',
            'Email': 'university_email',
            'Status': 'status',
            'Date of Joining': 'date_of_joining',
            'Academic Designation': 'academic_designation'
        }
        
        # Rename columns
        person_df = person_df.rename(columns=person_columns)
        faculty_df = faculty_df.rename(columns=faculty_columns)
        
        # Combine dataframes
        combined_df = pd.concat([person_df, faculty_df], axis=1)
        combined_df = combined_df.astype(object).where(pd.notnull(combined_df), None)
        
        return combined_df
        
    except Exception as e:
        raise CSVUploadError(f"Column standardization failed: {str(e)}", 400)


def parse_date_field(value) -> str:
    """Parse and format date fields for database"""
    if value is None or pd.isna(value) or value == "":
        return None
    
    try:
        if hasattr(value, 'isoformat'):  # datetime object
            return value.isoformat() if hasattr(value, 'date') else value.date().isoformat()
        
        # Parse string dates
        parsed_date = pd.to_datetime(value, errors='coerce')
        if pd.isna(parsed_date):
            return None
        return parsed_date.date().isoformat()
        
    except Exception:
        return None


async def handle_designations(session: AsyncSession, combined_df: pd.DataFrame) -> Dict[str, Designation]:
    """Handle designation creation and caching"""
    try:
        designation_titles = combined_df['academic_designation'].dropna().unique().tolist()
        if not designation_titles:
            return {}
        
        # Get existing designations
        stmt = select(Designation).where(Designation.title.in_(designation_titles))
        result = await session.execute(stmt)
        existing_designations = {d.title: d for d in result.scalars().all()}
        
        # Create new designations
        new_titles = [t for t in designation_titles if t not in existing_designations]
        if new_titles:
            new_designations = [
                Designation(title=title, type=DesignationType.academic) 
                for title in new_titles
            ]
            session.add_all(new_designations)
            await session.flush()
            
            # Update cache
            for designation in new_designations:
                existing_designations[designation.title] = designation
        
        return existing_designations
        
    except Exception as e:
        raise CSVUploadError(f"Designation handling failed: {str(e)}", 500)


async def handle_persons(session: AsyncSession, combined_df: pd.DataFrame) -> Dict[str, int]:
    """Handle person creation and return email to ID mapping"""
    try:
        person_fields = {
            'first_name', 'last_name', 'father_husband_name', 'sex', 'dob', 
            'cnic', 'cnic_expiry', 'phone', 'email', 'blood_group', 
            'marital_status', 'date_of_marriage', 'no_of_dependents'
        }
        
        # Prepare person records
        persons_to_insert = []
        for _, row in combined_df.iterrows():
            if not row.get('email'):
                continue
                
            person_data = {k: v for k, v in row.items() if k in person_fields}
            
            # Parse date fields
            date_fields = ['dob', 'cnic_expiry', 'date_of_marriage']
            for field in date_fields:
                if field in person_data:
                    person_data[field] = parse_date_field(person_data[field])
            
            persons_to_insert.append(person_data)
        
        if not persons_to_insert:
            raise CSVUploadError("No valid person records found with email addresses", 400)
        
        # Check for existing persons
        person_emails = [p['email'] for p in persons_to_insert]
        existing_result = await session.execute(
            select(Person.email).where(Person.email.in_(person_emails))
        )
        existing_emails = set(existing_result.scalars().all())
        
        # Insert only new persons
        new_persons = [p for p in persons_to_insert if p['email'] not in existing_emails]
        if new_persons:
            insert_stmt = pg_insert(Person.__table__).values(new_persons)
            await session.execute(insert_stmt)
        
        # Get person ID mapping
        result = await session.execute(
            select(Person.id, Person.email).where(Person.email.in_(person_emails))
        )
        return {row.email: row.id for row in result}
        
    except CSVUploadError:
        raise
    except Exception as e:
        raise CSVUploadError(f"Person processing failed: {str(e)}", 500)


async def handle_faculty(
    session: AsyncSession, 
    combined_df: pd.DataFrame, 
    person_id_map: Dict[str, int],
    designation_cache: Dict[str, Designation]
) -> int:
    """Handle faculty creation and return count of inserted records"""
    try:
        faculty_fields = {
            'code', 'title', 'university_email', 'status', 
            'date_of_joining', 'person_id', 'designation_id'
        }
        
        faculties_to_create = []
        for _, row in combined_df.iterrows():
            person_id = person_id_map.get(row.get('email'))
            if not person_id or not row.get('university_email'):
                continue
            
            # Prepare faculty data
            faculty_data = {k: v for k, v in row.items() if k in faculty_fields}
            faculty_data['person_id'] = person_id
            
            # Handle designation
            designation = designation_cache.get(row.get('academic_designation'))
            faculty_data['designation_id'] = designation.id if designation else None
            
            # Parse date
            faculty_data['date_of_joining'] = parse_date_field(faculty_data.get('date_of_joining'))
            
            # Handle code field
            code = faculty_data.get('code')
            if code is not None:
                try:
                    faculty_data['code'] = int(code)
                except (ValueError, TypeError):
                    faculty_data['code'] = person_id
            else:
                faculty_data['code'] = person_id
            
            faculties_to_create.append(faculty_data)
        
        if not faculties_to_create:
            return 0
        
        # Check for existing faculty
        emails = [f['university_email'] for f in faculties_to_create if f.get('university_email')]
        codes = [f['code'] for f in faculties_to_create if f.get('code')]
        
        existing_emails = set()
        existing_codes = set()
        
        if emails:
            result = await session.execute(
                select(Faculty.university_email).where(Faculty.university_email.in_(emails))
            )
            existing_emails = set(result.scalars().all())
        
        if codes:
            result = await session.execute(
                select(Faculty.code).where(Faculty.code.in_(codes))
            )
            existing_codes = set(result.scalars().all())
        
        # Filter out duplicates
        new_faculties = []
        for faculty in faculties_to_create:
            if (faculty.get('university_email') not in existing_emails and 
                faculty.get('code') not in existing_codes):
                new_faculties.append(faculty)
                existing_emails.add(faculty.get('university_email'))
                existing_codes.add(faculty.get('code'))
        
        # Insert new faculty
        if new_faculties:
            insert_stmt = pg_insert(Faculty.__table__).values(new_faculties)
            await session.execute(insert_stmt)
        
        return len(new_faculties)
        
    except Exception as e:
        raise CSVUploadError(f"Faculty processing failed: {str(e)}", 500)


async def handle_qualifications(
    session: AsyncSession, 
    original_df: pd.DataFrame, 
    person_id_map: Dict[str, int]
) -> int:
    """Handle qualification creation and return count of inserted records"""
    try:
        # Process qualifications
        qual_pipeline = QualificationDataPipeline()
        qual_result = qual_pipeline.process_pipeline(original_df, person_id_map)
        
        if not qual_result.get('success'):
            logger.warning(f"Qualification processing failed: {qual_result.get('message', 'Unknown error')}")
            return 0
        
        qualifications_to_create = qual_result.get('data', [])
        if not qualifications_to_create:
            return 0
        
        # Check for existing qualifications
        qual_check_data = [
            (q['person_id'], q['title']) 
            for q in qualifications_to_create 
            if q.get('person_id') and q.get('title')
        ]
        
        if qual_check_data:
            from sqlalchemy import and_, or_
            
            conditions = [
                and_(Qualification.person_id == person_id, Qualification.title == title)
                for person_id, title in qual_check_data
            ]
            
            if conditions:
                result = await session.execute(
                    select(Qualification.person_id, Qualification.title).where(or_(*conditions))
                )
                existing_quals = {(q.person_id, q.title) for q in result}
                
                # Filter new qualifications
                new_quals = [
                    q for q in qualifications_to_create 
                    if (q.get('person_id'), q.get('title')) not in existing_quals
                ]
                
                if new_quals:
                    insert_stmt = pg_insert(Qualification.__table__).values(new_quals)
                    await session.execute(insert_stmt)
                    return len(new_quals)
        
        return 0
        
    except Exception as e:
        logger.warning(f"Qualification processing failed: {str(e)}")
        return 0


@router.get("/faculty/all", response_model=List[FacultyOut])
async def get_all_faculty(
    session: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100
):
    """Get paginated faculty list"""
    try:
        stmt = select(Faculty).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching faculty: {e}")
        return create_error_response("Failed to fetch faculty data", 500)


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session)
):
    """Upload and process CSV/Excel files containing HR data"""
    tmp_path = None
    
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            return create_error_response("Invalid file type. Only CSV and Excel files are allowed.", 400)
        
        # Save and read file
        tmp_path = await save_uploaded_file(file)
        df = read_and_validate_file(tmp_path)
        
        # Process data
        processed_data = process_pipelines(df)
        combined_df = standardize_column_names(processed_data)
        
        # Database operations
        designation_cache = await handle_designations(session, combined_df)
        person_id_map = await handle_persons(session, combined_df)
        faculty_count = await handle_faculty(session, combined_df, person_id_map, designation_cache)
        qual_count = await handle_qualifications(session, df, person_id_map)
        
        # Commit transaction
        await session.commit()
        
        # Success response
        result_data = {
            "persons_processed": len(person_id_map),
            "faculty_inserted": faculty_count,
            "qualifications_inserted": qual_count,
            "total_rows": len(df)
        }
        
        message = f"Successfully processed {len(df)} rows. Inserted {faculty_count} faculty and {qual_count} qualifications."
        return create_success_response(result_data, message)
        
    except CSVUploadError as e:
        await session.rollback()
        return create_error_response(e.message, e.status_code)
    
    except IntegrityError as e:
        await session.rollback()
        return create_error_response("Data integrity violation. Check for duplicate records.", 409)
    
    except DatabaseError as e:
        await session.rollback()
        return create_error_response("Database error occurred.", 500)
    
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error: {e}")
        return create_error_response("An unexpected error occurred.", 500)
    
    finally:
        # Cleanup temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")