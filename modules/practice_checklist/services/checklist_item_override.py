"""
Service override de ejemplo.

Extiende PracticeChecklistItemService para que, cuando se marca el último ítem
como hecho, el checklist padre se cierre automáticamente (auto-close).

Esto demuestra cómo cambiar comportamiento de un servicio sin tocar el código
fuente original: se hereda, se sobreescribe el método y se registra la nueva
clase como servicio del modelo.
"""
from __future__ import annotations

import datetime as dt

from app.core.serializer import serialize
from app.core.services import exposed_action

from ..models import PracticeChecklist, PracticeChecklistItem
from ..services.checklist import PracticeChecklistItemService


class PracticeChecklistItemAutoCloseService(PracticeChecklistItemService):
    """Override que añade auto-cierre del checklist al completar todos los ítems."""

    @exposed_action("write", groups=["practice_checklist_group_manager", "core_group_superadmin"])
    def set_done(self, id: int, done: bool = True, note: str | None = None) -> dict:
        # Llamamos al método original para reutilizar toda su lógica
        result = super().set_done(id=id, done=done, note=note)

        # Solo evaluamos auto-close cuando se marca como hecho
        if done:
            item = self.repo.session.get(PracticeChecklistItem, int(id))
            if item and item.checklist_id:
                self._auto_close_if_all_done(item.checklist_id)

        return result

    def _auto_close_if_all_done(self, checklist_id: int) -> None:
        """Cierra el checklist si todos sus ítems están marcados como hechos."""
        checklist = self.repo.session.get(PracticeChecklist, checklist_id)
        if checklist is None or checklist.status == "closed":
            return

        pending = (
            self.repo.session.query(PracticeChecklistItem)
            .filter_by(checklist_id=checklist_id, is_done=False)
            .count()
        )
        if pending == 0:
            checklist.status = "closed"
            checklist.closed_at = dt.datetime.now(dt.timezone.utc)
            self.repo.session.add(checklist)
            self.repo.session.commit()
