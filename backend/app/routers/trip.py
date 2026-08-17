"""Trip HTTP routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models.staff import TripAnnouncement, TripAnnouncementRead, TripStaff
from app.db.models.trip import (
    TravelerAppFeedback,
    TripCancellationPolicy,
    TripEmergencyContact,
    TripFaq,
    TripRecommendation,
    TripTraveler,
)
from app.db.models.user import User
from app.services.qr_service import create_traveler_qr_payload
from app.services.service_agreement_service import resolve_service_agreement_url
from app.services.trip_service import (
    get_trip_phase_detail,
    get_trip_phases,
    get_trip_travelers,
)

router = APIRouter(tags=["trip"])


class AppFeedbackRequest(BaseModel):
    feedback: str = Field(max_length=5000)


@router.get("/me/trip")
async def get_my_trip(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the authenticated traveler's active trip info."""
    user_id = request.state.user_id

    result = await session.execute(
        text("""
            SELECT
                tt.wetravel_trip_uuid,
                wt.title,
                wt.destination,
                wt.start_date,
                wt.end_date,
                wt.url,
                wt.service_agreement_url
            FROM trip_travelers tt
            JOIN wetravel_trips wt ON wt.trip_uuid = tt.wetravel_trip_uuid
            WHERE tt.user_id = CAST(:user_id AS uuid)
              AND (wt.end_date IS NULL OR wt.end_date::date >= CURRENT_DATE)
            ORDER BY wt.start_date ASC
            LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.mappings().first()

    if not row:
        return {"trip": None}

    from app.services.trip_service import _get_trip_mode
    trip_uuid = row["wetravel_trip_uuid"]
    trip_mode = await _get_trip_mode(trip_uuid, session)
    return {
        "trip": {
            "wetravel_trip_uuid": trip_uuid,
            "title": row["title"],
            "destination": row["destination"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "url": row["url"],
            "service_agreement_url": resolve_service_agreement_url(row["service_agreement_url"]),
            "trip_mode": trip_mode,
        }
    }


@router.get("/me/qr-code")
async def get_my_qr_code(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the authenticated traveler's signed QR payload."""
    user_id = request.state.user_id

    result = await session.execute(
        text("""
            SELECT
                tt.id AS trip_traveler_id,
                tt.wetravel_trip_uuid
            FROM trip_travelers tt
            JOIN wetravel_trips wt ON wt.trip_uuid = tt.wetravel_trip_uuid
            WHERE tt.user_id = CAST(:user_id AS uuid)
              AND (wt.end_date IS NULL OR wt.end_date::date >= CURRENT_DATE)
            ORDER BY wt.start_date ASC NULLS LAST, tt.created_at ASC
            LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Viagem não encontrada para este usuário")

    trip_traveler_id = str(row["trip_traveler_id"])
    trip_uuid = row["wetravel_trip_uuid"]
    qr_payload = create_traveler_qr_payload(
        trip_traveler_id=trip_traveler_id,
        trip_uuid=trip_uuid,
    )

    return {
        "trip_uuid": trip_uuid,
        "trip_traveler_id": trip_traveler_id,
        "qr_payload": qr_payload,
    }


@router.get("/me/trip/phases")
async def get_my_trip_phases(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Retorna todas as fases da viagem do usuário autenticado."""
    return await get_trip_phases(request.state.user_id, session)


@router.get("/me/trip/phases/{phase_id}")
async def get_my_trip_phase_detail(
    phase_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Retorna uma fase específica com atividades."""
    return await get_trip_phase_detail(request.state.user_id, phase_id, session)


@router.get("/me/trip/travelers")
async def get_my_trip_travelers(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Retorna todos os viajantes do mesmo trip com fase atual de cada um."""
    return await get_trip_travelers(request.state.user_id, session)


async def _get_traveler_trip_uuid(user_id: str, session: AsyncSession) -> str:
    result = await session.execute(
        text("""
            SELECT tt.wetravel_trip_uuid
            FROM trip_travelers tt
            JOIN wetravel_trips wt ON wt.trip_uuid = tt.wetravel_trip_uuid
            WHERE tt.user_id = CAST(:user_id AS uuid)
              AND (wt.end_date IS NULL OR wt.end_date::date >= CURRENT_DATE)
            ORDER BY wt.start_date ASC
            LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="No active trip found")
    return row["wetravel_trip_uuid"]


async def _get_active_trip_traveler(user_id: str, session: AsyncSession) -> TripTraveler:
    result = await session.execute(
        text("""
            SELECT tt.id
            FROM trip_travelers tt
            JOIN wetravel_trips wt ON wt.trip_uuid = tt.wetravel_trip_uuid
            WHERE tt.user_id = CAST(:user_id AS uuid)
              AND (wt.end_date IS NULL OR wt.end_date::date >= CURRENT_DATE)
            ORDER BY wt.start_date ASC
            LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="No active trip found")

    trip_traveler = await session.get(TripTraveler, row["id"])
    if trip_traveler is None:
        raise HTTPException(status_code=404, detail="No active trip found")
    return trip_traveler


@router.get("/me/announcements")
async def get_my_announcements(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return trip announcements for the authenticated traveler, newest first."""
    user_id = request.state.user_id
    user_uuid = uuid.UUID(user_id)
    trip_uuid = await _get_traveler_trip_uuid(user_id, session)

    rows = (await session.execute(
        select(TripAnnouncement, User.full_name, TripAnnouncementRead.id)
        .join(User, User.id == TripAnnouncement.sent_by_user_id)
        .outerjoin(
            TripAnnouncementRead,
            (TripAnnouncementRead.announcement_id == TripAnnouncement.id)
            & (TripAnnouncementRead.user_id == user_uuid),
        )
        .where(TripAnnouncement.wetravel_trip_uuid == trip_uuid)
        .order_by(TripAnnouncement.created_at.desc())
    )).all()
    unread_count = sum(1 for _, _, read_id in rows if read_id is None)

    return {
        "unread_count": unread_count,
        "announcements": [
            {
                "id": str(ann.id),
                "title": ann.title,
                "body": ann.body,
                "sent_by": "Parrot Team" if ann.is_anonymous else name,
                "created_at": ann.created_at.isoformat(),
                "is_read": read_id is not None,
            }
            for ann, name, read_id in rows
        ]
    }


@router.post("/me/announcements/{announcement_id}/read")
async def mark_my_announcement_read(
    announcement_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Mark one announcement as read for the authenticated traveler."""
    user_id = request.state.user_id
    user_uuid = uuid.UUID(user_id)
    trip_uuid = await _get_traveler_trip_uuid(user_id, session)

    announcement = await session.scalar(
        select(TripAnnouncement).where(
            TripAnnouncement.id == announcement_id,
            TripAnnouncement.wetravel_trip_uuid == trip_uuid,
        )
    )
    if announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    existing_read = await session.scalar(
        select(TripAnnouncementRead).where(
            TripAnnouncementRead.announcement_id == announcement_id,
            TripAnnouncementRead.user_id == user_uuid,
        )
    )
    if existing_read is None:
        session.add(TripAnnouncementRead(announcement_id=announcement_id, user_id=user_uuid))
        await session.commit()

    return {"status": "read", "announcement_id": str(announcement_id)}


@router.get("/me/app-feedback")
async def get_my_app_feedback(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return the authenticated traveler's editable app feedback for the active trip."""
    trip_traveler = await _get_active_trip_traveler(request.state.user_id, session)
    feedback = await session.scalar(
        select(TravelerAppFeedback).where(TravelerAppFeedback.trip_traveler_id == trip_traveler.id)
    )

    return {"feedback": feedback.feedback if feedback else None}


@router.put("/me/app-feedback")
async def update_my_app_feedback(
    body: AppFeedbackRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Create or update one app feedback entry for the authenticated traveler and active trip."""
    trip_traveler = await _get_active_trip_traveler(request.state.user_id, session)
    feedback = await session.scalar(
        select(TravelerAppFeedback).where(TravelerAppFeedback.trip_traveler_id == trip_traveler.id)
    )
    text_value = body.feedback.strip()

    if feedback is None:
        feedback = TravelerAppFeedback(trip_traveler_id=trip_traveler.id, feedback=text_value)
        session.add(feedback)
    else:
        feedback.feedback = text_value

    await session.commit()
    await session.refresh(feedback)

    return {
        "feedback": feedback.feedback,
        "updated_at": feedback.updated_at.isoformat(),
    }


@router.get("/me/team")
async def get_my_team(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return Parrot staff members assigned to the traveler's active trip."""
    user_id = request.state.user_id
    trip_uuid = await _get_traveler_trip_uuid(user_id, session)

    # Primary: read from trip_staff (has function, photo_url, bio)
    staff_rows = (await session.execute(
        select(TripStaff, User.full_name, User.phone)
        .join(User, User.id == TripStaff.user_id)
        .where(TripStaff.wetravel_trip_uuid == trip_uuid)
        .order_by(User.full_name)
    )).all()

    if staff_rows:
        return {
            "team": [
                {
                    "id": str(ts.id),
                    "name": name,
                    "function": ts.function,
                    "phone": phone,
                    "photo_url": ts.photo_url,
                    "bio": ts.bio,
                }
                for ts, name, phone in staff_rows
            ]
        }

@router.get("/me/emergency-contacts")
async def get_my_emergency_contacts(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return emergency contacts for the traveler's active trip."""
    user_id = request.state.user_id
    trip_uuid = await _get_traveler_trip_uuid(user_id, session)

    rows = (await session.execute(
        select(TripEmergencyContact)
        .where(TripEmergencyContact.wetravel_trip_uuid == trip_uuid)
        .order_by(TripEmergencyContact.sort_order)
    )).scalars().all()

    return {
        "emergency_contacts": [
            {
                "id": str(r.id),
                "name": r.name,
                "role": r.role,
                "phone": r.phone,
                "sort_order": r.sort_order,
            }
            for r in rows
        ]
    }


@router.get("/me/recommendations")
async def get_my_recommendations(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return local recommendations for the traveler's active trip."""
    user_id = request.state.user_id
    trip_uuid = await _get_traveler_trip_uuid(user_id, session)

    rows = (await session.execute(
        select(TripRecommendation)
        .where(TripRecommendation.wetravel_trip_uuid == trip_uuid)
        .order_by(TripRecommendation.sort_order)
    )).scalars().all()

    return {
        "recommendations": [
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "address": r.address,
                "photo_url": r.photo_url,
                "sort_order": r.sort_order,
                "category": r.category,
                "neighborhood": r.neighborhood,
                "location": r.location,
                "highlight": r.highlight,
                "price_range": r.price_range,
                "rating": float(r.rating) if r.rating is not None else None,
                "map_url": r.map_url,
                "emoji": r.emoji,
                "phone": r.phone,
                "whatsapp_url": r.whatsapp_url,
                "contact_label": r.contact_label,
            }
            for r in rows
        ]
    }


@router.get("/me/faq")
async def get_my_faq(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return FAQ items for the traveler's active trip."""
    user_id = request.state.user_id
    trip_uuid = await _get_traveler_trip_uuid(user_id, session)

    rows = (await session.execute(
        select(TripFaq)
        .where(TripFaq.wetravel_trip_uuid == trip_uuid)
        .order_by(TripFaq.sort_order)
    )).scalars().all()

    return {
        "faq": [
            {"id": str(r.id), "question": r.question, "answer": r.answer, "sort_order": r.sort_order}
            for r in rows
        ]
    }


@router.get("/me/cancellation-policy")
async def get_my_cancellation_policy(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return cancellation policy items for the traveler's active trip."""
    user_id = request.state.user_id
    trip_uuid = await _get_traveler_trip_uuid(user_id, session)

    rows = (await session.execute(
        select(TripCancellationPolicy)
        .where(TripCancellationPolicy.wetravel_trip_uuid == trip_uuid)
        .order_by(TripCancellationPolicy.sort_order)
    )).scalars().all()

    return {
        "cancellation_policy": [
            {"id": str(r.id), "title": r.title, "body": r.body, "sort_order": r.sort_order}
            for r in rows
        ]
    }


    # Fallback: trip_staff empty, use trip_travelers with role=staff
    traveler_rows = (await session.execute(
        select(TripTraveler, User.full_name, User.phone)
        .join(User, User.id == TripTraveler.user_id)
        .where(
            TripTraveler.wetravel_trip_uuid == trip_uuid,
            User.role == "staff",
        )
        .order_by(User.full_name)
    )).all()

    return {
        "team": [
            {
                "id": str(tt.id),
                "name": name,
                "function": None,
                "phone": phone,
                "photo_url": None,
                "bio": None,
            }
            for tt, name, phone in traveler_rows
        ]
    }
