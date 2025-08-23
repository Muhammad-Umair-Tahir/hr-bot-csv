from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy import select
from schemas.schema import FacultyOut
from sqlalchemy.ext.asyncio import AsyncSession
from models.person_model import Person
from models.faculty_model import Faculty
from models.education_model import Qualification
from models.designation_model import Designation, DesignationType
from utils.csv_cleaner import PersonDataPipeline
from utils.faculty_details import FacultyDataPipeline
from database.connect import get_db_session
import numpy as np
import pandas as pd
import tempfile
import asyncio
import datetime

router = APIRouter()

# Fast faculty GET endpoint
@router.get("/faculty/all", response_model=list[FacultyOut])
async def get_all_faculty(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Faculty))
    faculty_list = result.scalars().all()
    return faculty_list

@router.post("/upload-csv/")
async def upload_csv(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session)
):
    # Save uploaded file to a temp file
    try:
        suffix = ".xlsx" if file.filename.endswith(".xlsx") else ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save uploaded file: {e}")

    # Extract and clean data
    person_pipeline = PersonDataPipeline()
    faculty_pipeline = FacultyDataPipeline()
    
    person_df = person_pipeline.process_pipeline(tmp_path)['cleaned_data']
    faculty_df = faculty_pipeline.process_pipeline(tmp_path)['cleaned_data']
    
    # Map person_df columns to match Person model fields
    person_column_map = {
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
        'No. of Dependendts': 'no_of_dependents',
    }
    
    person_df = person_df.rename(columns=person_column_map)
    
    # Map faculty_df columns to match Faculty model fields
    faculty_column_map = {
        'Code': 'code',
        'Title': 'title',
        'Email': 'university_email',
        'Status': 'status',
        'Date of Joining': 'date_of_joining',
        'Academic Designation': 'academic_designation'
    }
    
    faculty_df = faculty_df.rename(columns=faculty_column_map)
    
    # Read the full CSV for qualification extraction
    try:
        if tmp_path.endswith('.xlsx'):
            full_df = pd.read_excel(tmp_path)
        else:
            full_df = pd.read_csv(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV for qualification extraction: {e}")

    if len(person_df) != len(faculty_df) or len(person_df) != len(full_df):
        raise HTTPException(status_code=400, detail="Row count mismatch between person, faculty, and qualification data.")

    inserted = 0
    skipped = 0
    skipped_entries = []
    
    date_fields = ["dob", "cnic_expiry", "date_of_marriage"]
    
    def parse_date(val):
        if val is None or pd.isna(val) or val == "":
            return None
        if isinstance(val, datetime.date):
            return val
        try:
            return pd.to_datetime(val, errors="coerce").date()
        except Exception:
            return None

    faculty_model_fields = {
        'code', 'title', 'university_email', 'designation_id', 'track_id', 'status', 'person_id',
        'department_id', 'school_id', 'date_of_joining'
    }
    
    from sqlalchemy.exc import IntegrityError
    
    for idx, (person_row, faculty_row) in enumerate(zip(
        person_df.to_dict(orient='records'),
        faculty_df.to_dict(orient='records'))):
        
        # Convert date fields in person_row
        for field in date_fields:
            if field in person_row:
                person_row[field] = parse_date(person_row[field])
        
        # Create person record
        person = Person(**person_row)
        session.add(person)
        await session.flush()
        person_id = person.id

        # Handle designation: use academic_designation as primary
        academic_title = faculty_row.get('academic_designation', 'Unknown')
        designation_id = None
        
        if academic_title and academic_title != 'Unknown':
            # Check if designation exists
            result = await session.execute(
                select(Designation).where(
                    Designation.title == academic_title,
                    Designation.type == DesignationType.academic
                )
            )
            designation = result.scalar_one_or_none()
            
            if not designation:
                # Create new designation
                designation = Designation(title=academic_title, type=DesignationType.academic)
                session.add(designation)
                await session.flush()
            
            designation_id = designation.id

        faculty_row['person_id'] = person_id
        faculty_row['designation_id'] = designation_id
        
        # Remove academic_designation from faculty_row since it's not a column in Faculty table
        if 'academic_designation' in faculty_row:
            del faculty_row['academic_designation']
        
        # Sanitize integer fields (e.g., code) before model instantiation
        int_fields = ['code', 'designation_id', 'track_id', 'person_id', 'department_id', 'school_id']
        for field in int_fields:
            if field in faculty_row:
                val = faculty_row[field]
                if val in [None, '', 'N/A']:
                    # Set unique default value for code if missing
                    if field == 'code':
                        faculty_row[field] = person_id  # Use unique person_id as fallback
                    else:
                        faculty_row[field] = None
                else:
                    try:
                        faculty_row[field] = int(val)
                    except Exception:
                        faculty_row[field] = person_id if field == 'code' else None

        # Filter faculty_row to only valid model fields
        filtered_faculty_row = {k: v for k, v in faculty_row.items() if k in faculty_model_fields}
        
        faculty = Faculty(**filtered_faculty_row)
        
        try:
            session.add(faculty)
            await session.commit()
            inserted += 1
        except IntegrityError as e:
            await session.rollback()
            if 'duplicate key value violates unique constraint' in str(e):
                skipped += 1
                skipped_entries.append({
                    'row': idx + 1,
                    'code': filtered_faculty_row.get('code'),
                    'reason': 'Duplicate faculty code, entry skipped.'
                })
                continue
            else:
                raise

    result = {"message": f"Successfully inserted {inserted} person/faculty sets."}
    
    if skipped > 0:
        result["skipped"] = skipped
        result["skipped_entries"] = skipped_entries
    
    return result
