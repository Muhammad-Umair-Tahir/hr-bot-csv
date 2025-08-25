from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
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
import os
import traceback
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("csv_upload_router")

router = APIRouter()

# Custom error handler for CSV upload process
def handle_upload_error(stage: str, error: Exception, status_code: int = 400):
    """
    Create a standardized error response for CSV upload errors.
    
    Args:
        stage: The stage of the upload process where the error occurred
        error: The exception that was raised
        status_code: The HTTP status code to return
        
    Returns:
        JSONResponse with error details
    """
    error_detail = str(error)
    error_trace = traceback.format_exc()
    
    logger.error(f"CSV upload error at stage '{stage}': {error_detail}")
    logger.debug(error_trace)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "stage": stage,
                "message": error_detail,
                "type": error.__class__.__name__
            }
        }
    )

# Fast faculty GET endpoint
@router.get("/faculty/all", response_model=list[FacultyOut])
async def get_all_faculty(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Faculty))
    faculty_list = result.scalars().all()
    return faculty_list

@router.post("/upload-csv", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session)
):
    tmp_path = None
    try:
        # Step 1: Save uploaded file to a temp file
        try:
            suffix = ".xlsx" if file.filename.endswith(".xlsx") else ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                contents = await file.read()
                tmp.write(contents)
                tmp_path = tmp.name
                logger.info(f"File {file.filename} saved temporarily as {tmp_path}")
        except Exception as e:
            return handle_upload_error("file_saving", e)

        # Step 2: Extract and clean person data
        try:
            person_pipeline = PersonDataPipeline()
            person_pipeline_result = person_pipeline.process_pipeline(tmp_path)
            
            if person_pipeline_result is None or 'cleaned_data' not in person_pipeline_result:
                # Try to read the file directly to provide better error information
                try:
                    if tmp_path.endswith('.xlsx'):
                        sample_df = pd.read_excel(tmp_path)
                    else:
                        sample_df = pd.read_csv(tmp_path)
                    columns_info = ", ".join(sample_df.columns.tolist())
                    error_msg = f"Person pipeline failed to process the file. File contains columns: {columns_info}"
                    raise ValueError(error_msg)
                except Exception as read_error:
                    error_msg = f"Person pipeline failed and file cannot be read: {str(read_error)}"
                    raise ValueError(error_msg)
            
            if not person_pipeline_result['success']:
                raise ValueError(person_pipeline_result['message'])
                
            person_df = person_pipeline_result['cleaned_data']
            logger.info(f"Person data processed successfully: {len(person_df)} rows")
        except Exception as e:
            return handle_upload_error("person_data_processing", e)
        
        # Step 3: Extract and clean faculty data
        try:
            faculty_pipeline = FacultyDataPipeline()
            faculty_pipeline_result = faculty_pipeline.process_pipeline(tmp_path)
            
            if faculty_pipeline_result is None or 'cleaned_data' not in faculty_pipeline_result:
                raise ValueError("Faculty pipeline failed to process the file")
            
            if not faculty_pipeline_result['success']:
                raise ValueError(faculty_pipeline_result['message'])
                
            faculty_df = faculty_pipeline_result['cleaned_data']
            logger.info(f"Faculty data processed successfully: {len(faculty_df)} rows")
        except Exception as e:
            return handle_upload_error("faculty_data_processing", e)
        
        # Step 4: Map columns and prepare data
        try:
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
            if tmp_path.endswith('.xlsx'):
                full_df = pd.read_excel(tmp_path)
            else:
                full_df = pd.read_csv(tmp_path)
                
            # Verify row counts match
            if len(person_df) != len(faculty_df) or len(person_df) != len(full_df):
                raise ValueError(f"Row count mismatch between person ({len(person_df)}), faculty ({len(faculty_df)}), and raw data ({len(full_df)}).")
                
            logger.info("Data prepared successfully for database insertion")
        except Exception as e:
            return handle_upload_error("data_preparation", e)
        
        # Step 5: Insert data into database
        try:
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
            
            # Process each row as a transaction
            for idx, (person_row, faculty_row) in enumerate(zip(
                person_df.to_dict(orient='records'),
                faculty_df.to_dict(orient='records'))):
                
                try:
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
                    
                    session.add(faculty)
                    await session.commit()
                    inserted += 1
                    logger.debug(f"Inserted row {idx+1} successfully")
                
                except IntegrityError as e:
                    await session.rollback()
                    if 'duplicate key value violates unique constraint' in str(e):
                        skipped += 1
                        skipped_entries.append({
                            'row': idx + 1,
                            'code': faculty_row.get('code'),
                            'reason': f'Duplicate key violation: {str(e)}'
                        })
                        logger.warning(f"Skipped row {idx+1} due to duplicate key: {faculty_row.get('code')}")
                    else:
                        logger.error(f"Database integrity error on row {idx+1}: {str(e)}")
                        raise
                
                except Exception as row_error:
                    await session.rollback()
                    skipped += 1
                    skipped_entries.append({
                        'row': idx + 1,
                        'code': faculty_row.get('code', 'unknown'),
                        'reason': f'Error processing row: {str(row_error)}'
                    })
                    logger.error(f"Error processing row {idx+1}: {str(row_error)}")
            
            logger.info(f"Database insertion complete: {inserted} inserted, {skipped} skipped")
            
            # Prepare success response
            result = {
                "success": True,
                "message": f"Successfully inserted {inserted} person/faculty sets.",
                "data": {
                    "inserted": inserted,
                    "total": len(person_df)
                }
            }
            
            if skipped > 0:
                result["skipped"] = skipped
                result["skipped_entries"] = skipped_entries
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=result
            )
            
        except Exception as e:
            return handle_upload_error("database_insertion", e, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        # Catch-all for any unhandled exceptions
        return handle_upload_error("unknown", e, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    finally:
        # Clean up temp file if it exists
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.debug(f"Temporary file {tmp_path} deleted")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {tmp_path}: {str(e)}")
