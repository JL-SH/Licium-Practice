from __future__ import annotations
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.fields import field

class Event(Base):
    __tablename__ = "community_events_event"
    __abstract__ = False
    __model__ = "event"
    __service__ = "modules.community_events.services.events.EventService"

    title = field(String(200), required=True, public=True, editable=True, info = {"label": "Título del evento"})
    slug = field(String(200), required=True, public=True, editable=True, info = {"label": "Enlace"})
    summary = field(String(500), required=False, public=True, editable=True, info = {"label": "Resumen"})
    description = field(Text, required=False, public=True, editable=True, info = {"label": "Descripción"})
    status = field(
        String(20), required=True, default="draft", public=True, editable=True,
        info={"choices": [
            {"label": "Borrador", "value": "draft"},
            {"label": "Publicado", "value": "published"},
            {"label": "Cerrado", "value": "closed"},
            {"label": "Cancelado", "value": "cancelled"}
        ]}
    )
    start_at = field(DateTime(timezone=True), required=True, public=True, editable=True, info = {"label": "Comienzo"})
    end_at = field(DateTime(timezone=True), required=True, public=True, editable=True, info = {"label": "Termina"})
    location = field(String(255), required=False, public=True, editable=True, info = {"label": "Localización"})
    capacity_total = field(Integer, required=True, default=0, public=True, editable=True, info = {"label": "Capacidad total"})
    is_public = field(Boolean, required=True, default=False, public=True, editable=True, info = {"label": "Evento público"})
    organizer_user_id = field(UUID, ForeignKey("core_user.id"), required=False, public=True, editable=True, info = {"label": "Organizado por"})

    sessions = relationship("modules.community_events.models.events.Session", cascade="all, delete-orphan")
    registrations = relationship("modules.community_events.models.events.Registration", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "community_events_session"
    __abstract__ = False
    __model__ = "session"
    __service__ = "modules.community_events.services.events.SessionService"

    event_id = field(Integer, ForeignKey("community_events_event.id", ondelete="CASCADE"), required=True, public=True, editable=True)
    title = field(String(200), required=True, public=True, editable=True)
    start_at = field(DateTime(timezone=True), required=True, public=True, editable=True)
    end_at = field(DateTime(timezone=True), required=True, public=True, editable=True)
    speaker_name = field(String(150), required=False, public=True, editable=True)
    room = field(String(100), required=False, public=True, editable=True)
    capacity = field(Integer, required=False, public=True, editable=True)
    status = field(String(20), required=True, default="active", public=True, editable=True)


class Registration(Base):
    __tablename__ = "community_events_registration"
    __abstract__ = False
    __model__ = "registration"
    __service__ = "modules.community_events.services.events.RegistrationService"

    event_id = field(Integer, ForeignKey("community_events_event.id", ondelete="CASCADE"), required=True, public=True, editable=True)
    session_id = field(Integer, ForeignKey("community_events_session.id", ondelete="SET NULL"), required=False, public=True, editable=True)
    
    attendee_name = field(String(150), required=True, public=True, editable=True)
    attendee_email = field(String(150), required=True, public=True, editable=True)
    attendee_user_id = field(UUID, ForeignKey("core_user.id", ondelete="SET NULL"), required=False, public=True, editable=True)
    
    status = field(
        String(20), required=True, default="pending", public=True, editable=True,
        info={"choices": [
            {"label": "Pendiente", "value": "pending"},
            {"label": "Confirmado", "value": "confirmed"},
            {"label": "Lista de Espera", "value": "waitlist"},
            {"label": "Cancelado", "value": "cancelled"}
        ]}
    )
    registered_at = field(DateTime(timezone=True), required=False, public=True, editable=False)
    checkin_at = field(DateTime(timezone=True), required=False, public=True, editable=False)
    notes = field(Text, required=False, public=True, editable=True)