from __future__ import annotations
import datetime as dt
from fastapi import HTTPException
from app.core.base import BaseService
from app.core.serializer import serialize
from app.core.services import exposed_action

class SessionService(BaseService):
    from ..models.events import Session

class EventService(BaseService):
    from ..models.events import Event

    def sanitize_dates(self, payload: dict) -> dict:
        import datetime as dt
        for key in ("start_at", "end_at"):
            raw_value = payload.get(key)
            if raw_value and isinstance(raw_value, str) and "/" in raw_value:
                try:
                    converted = dt.datetime.strptime(raw_value.split()[0], "%d/%m/%Y")
                    payload[key] = converted.replace(tzinfo=dt.timezone.utc)
                except ValueError:
                    pass
        return payload

    def create(self, obj):  # type: ignore[override]
        if not isinstance(obj, dict):
            return super().create(obj)
        data_copy = self.sanitize_dates(dict(obj))
        return super().create(data_copy)

    def update(self, id: int, obj):  # type: ignore[override]
        if not isinstance(obj, dict):
            return super().update(id, obj)
        data_copy = self.sanitize_dates(dict(obj))
        return super().update(id, data_copy)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def publish_event(self, id: int, note: str | None = None) -> dict:
        record = self.repo.session.get(self.Event, int(id))
        if record is None:
            raise HTTPException(404, "No se encontró el evento solicitado")

        record.status = "published"
        record.is_public = True
        self.repo.session.add(record)
        self.repo.session.commit()
        return serialize(record)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def close_registration(self, id: int, reason: str | None = None) -> dict:
        record = self.repo.session.get(self.Event, int(id))
        if record is None:
            raise HTTPException(404, "El evento indicado no existe")

        record.status = "closed"
        self.repo.session.add(record)
        self.repo.session.commit()
        return serialize(record)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def cancel_event(self, id: int, reason: str) -> dict:
        record = self.repo.session.get(self.Event, int(id))
        if record is None:
            raise HTTPException(404, "El evento especificado no fue hallado")

        record.status = "cancelled"
        record.is_public = False
        self.repo.session.add(record)
        self.repo.session.commit()
        return serialize(record)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def reopen_event(self, id: int) -> dict:
        record = self.repo.session.get(self.Event, int(id))
        if record is None:
            raise HTTPException(404, "No existe un evento con ese identificador")

        record.status = "published"
        record.is_public = True
        self.repo.session.add(record)
        self.repo.session.commit()
        return serialize(record)


class RegistrationService(BaseService):
    from ..models.events import Registration

    def create(self, obj):
        if not isinstance(obj, dict):
            return super().create(obj)
        entry = dict(obj)
        entry["registered_at"] = dt.datetime.now(dt.timezone.utc)
        if "status" not in entry:
            entry["status"] = "pending"
        return super().create(entry)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def confirm(self, id: int, note: str | None = None) -> dict:
        record = self.repo.session.get(self.Registration, int(id))
        if record is None:
            raise HTTPException(404, "No se encontró la inscripción indicada")
        record.status = "confirmed"
        if note:
            record.notes = f"{record.notes or ''} | {note}".strip()
        self.repo.session.add(record)
        self.repo.session.commit()
        return serialize(record)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def move_waitlist(self, id: int, note: str | None = None) -> dict:
        record = self.repo.session.get(self.Registration, int(id))
        if record is None:
            raise HTTPException(404, "La inscripción solicitada no existe")
        record.status = "waitlist"
        self.repo.session.add(record)
        self.repo.session.commit()
        return serialize(record)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def checkin(self, id: int, source: str = "manual") -> dict:
        record = self.repo.session.get(self.Registration, int(id))
        if record is None:
            raise HTTPException(404, "No se pudo localizar la inscripción")
        if record.status not in ["confirmed", "pending"]:
            raise HTTPException(400, "El estado actual del registro no permite el acceso.")

        record.checkin_at = dt.datetime.now(dt.timezone.utc)
        record.notes = f"{record.notes or ''} [Checkin: {source}]".strip()
        self.repo.session.add(record)
        self.repo.session.commit()
        return serialize(record)

    @exposed_action("write", groups=["community_events_group_staff", "core_group_superadmin"])
    def bulk_checkin(self, ids: list[int]) -> dict:
        validated = 0
        for reg_id in ids:
            entry = self.repo.session.get(self.Registration, int(reg_id))
            if entry and entry.status in ["confirmed", "pending"] and not entry.checkin_at:
                entry.checkin_at = dt.datetime.now(dt.timezone.utc)
                entry.notes = f"{entry.notes or ''} [Bulk Checkin]".strip()
                self.repo.session.add(entry)
                validated += 1
        self.repo.session.commit()
        return {"message": f"Se procesaron {validated} registros de acceso."}