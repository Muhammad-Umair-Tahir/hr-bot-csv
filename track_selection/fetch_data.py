from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any
from models.faculty_model import Faculty
from models.tracks_model import Track
from models.person_model import Person
from database.connect import get_async_session_maker
import logging

logger = logging.getLogger(__name__)


async def fetch_faculty_and_track_data(faculty_id: int, track_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch specific faculty and track data using their IDs.
    
    Args:
        faculty_id (int): The ID of the faculty to fetch
        track_id (int): The ID of the track to fetch
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing:
            - faculty_data: name, code, academic_designation, administrative_designation, teaching_experience, professional_experience, university_email, status, role, is_active
            - track_data: code, name, type
            Returns None if either faculty or track not found
    """
    session_maker = get_async_session_maker()
    
    try:
        async with session_maker() as session:
            # Fetch faculty with person relationship (no designation relationship needed)
            faculty_query = (
                select(Faculty)
                .options(selectinload(Faculty.person))
                .where(Faculty.id == faculty_id)
            )
            
            # Fetch track data
            track_query = (
                select(Track)
                .where(Track.id == track_id)
            )
            
            # Execute both queries
            faculty_result = await session.execute(faculty_query)
            track_result = await session.execute(track_query)
            
            faculty = faculty_result.scalar_one_or_none()
            track = track_result.scalar_one_or_none()
            
            # Check if both records exist
            if not faculty:
                logger.warning(f"No faculty found with ID: {faculty_id}")
                return None
                
            if not track:
                logger.warning(f"No track found with ID: {track_id}")
                return None
            
            # Build faculty name from person data
            faculty_name = None
            if faculty.person:
                faculty_name = f"{faculty.person.first_name} {faculty.person.last_name}"
            
            # Prepare the result dictionary with direct designation fields
            result = {
                "faculty_data": {
                    "title": faculty.title,
                    "name": faculty_name,
                    "code": faculty.code,
                    "academic_designation": faculty.academic_designation,  # Direct field from faculty table
                    "administrative_designation": faculty.administrative_designation,  # Direct field from faculty table
                    "teaching_experience": faculty.teaching_experience,  # Years of teaching experience
                    "professional_experience": faculty.professional_experience,  # Years of professional experience
                    "university_email": faculty.university_email,
                    "status": faculty.status,
                    "role": faculty.role.value if faculty.role else None,
                    "is_active": faculty.is_active
                },
                "track_data": {
                    "code": track.code,
                    "name": track.name,
                    "type": track.track_type.value if track.track_type else None
                }
            }
            
            logger.info(f"Successfully fetched data for faculty ID: {faculty_id} and track ID: {track_id}")
            return result
                
    except Exception as e:
        logger.error(f"Error fetching faculty (ID: {faculty_id}) and track (ID: {track_id}) data: {str(e)}")
        raise


# Test function
async def test_fetch_function():
    """
    Test function to demonstrate usage.
    """
    try:
        # Example usage - replace with actual IDs
        result = await fetch_faculty_and_track_data(faculty_id=4249, track_id=2)
        
        if result:
            print("Faculty Data:")
            for key, value in result["faculty_data"].items():
                print(f"  {key}: {value}")
            
            print("\nTrack Data:")
            for key, value in result["track_data"].items():
                print(f"  {key}: {value}")
        else:
            print("No data found for the given IDs")
            
    except Exception as e:
        print(f"Error in test function: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_fetch_function())