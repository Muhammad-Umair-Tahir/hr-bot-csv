from __future__ import annotations
import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.faculty_track_assignment_model import (
	FacultyTrackAssignment,
	Status as AssignmentStatus,
)
from models.academic_year_model import AcademicYear


# Note: AI decisions should not set approved_by/approved_on. HR will set those explicitly.


async def _resolve_academic_year_id(session: AsyncSession, provided_id: Optional[int]) -> int:
	if provided_id:
		ay = await session.get(AcademicYear, provided_id)
		if not ay:
			raise ValueError(f"AcademicYear id={provided_id} not found")
		return ay.id

	# Prefer is_current
	res = await session.execute(select(AcademicYear).where(AcademicYear.is_current == True))
	ay = res.scalars().first()
	if ay:
		return ay.id

	# Fallback to date range containment
	today = datetime.date.today()
	res = await session.execute(
		select(AcademicYear).where(AcademicYear.start_date <= today, AcademicYear.end_date >= today)
	)
	ay = res.scalars().first()
	if ay:
		return ay.id

	raise ValueError("No current academic year found; please provide academic_year_id explicitly")


def _map_decision_to_status(decision: str) -> AssignmentStatus:
	d = (decision or "").strip().upper()
	return AssignmentStatus.approved if d == "APPROVED" else AssignmentStatus.rejected


async def save_faculty_track_decision(
	session: AsyncSession,
	*,
	faculty_id: int,
	track_id: int,
	decision: str,
	remarks: str,
	academic_year_id: Optional[int] = None,
	track_level_id: Optional[int] = None,
) -> FacultyTrackAssignment:
	"""Upsert a FacultyTrackAssignment for (faculty_id, academic_year_id) with AI decision.

	- Resolves academic_year_id if not provided.
	- Maps decision to approved/rejected.
	- Does NOT set approved_by/approved_on; those are reserved for HR approvals.
	- Updates existing row or creates a new one.
	"""

	ay_id = await _resolve_academic_year_id(session, academic_year_id)
	status = _map_decision_to_status(decision)
	today = datetime.date.today()

	async def _upsert() -> FacultyTrackAssignment:
		res = await session.execute(
			select(FacultyTrackAssignment).where(
				FacultyTrackAssignment.faculty_id == faculty_id,
				FacultyTrackAssignment.academic_year_id == ay_id,
			)
		)
		entity = res.scalars().first()
		if entity is None:
			entity = FacultyTrackAssignment(
				faculty_id=faculty_id,
				academic_year_id=ay_id,
				track_id=track_id,
				track_level_id=track_level_id,
				remarks=remarks,
				status=status,
				submitted_on=today,
			)
			session.add(entity)
		else:
			entity.track_id = track_id
			entity.track_level_id = track_level_id
			entity.remarks = remarks
			entity.status = status
			entity.submitted_on = today
			# Do not modify approved_by/approved_on here; keep HR approvals intact
		return entity

	try:
		entity = await _upsert()
		await session.commit()
		await session.refresh(entity)
		return entity
	except IntegrityError:
		await session.rollback()
		entity = await _upsert()
		await session.commit()
		await session.refresh(entity)
		return entity
