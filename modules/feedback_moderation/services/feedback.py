from __future__ import annotations
import datetime as dt
from fastapi import HTTPException
from app.core.base import BaseService
from app.core.serializer import serialize
from app.core.services import exposed_action
from app.core.context import get_current_user_id

class TagService(BaseService):
    from ..models.feedback import Tag

class SuggestionService(BaseService):
    from ..models.feedback import Suggestion

    def create(self, obj):  
        if not isinstance(obj, dict): return super().create(obj)
        clean_payload = dict(obj)
        clean_payload["status"] = "pending"
        clean_payload["is_public"] = False
        return super().create(clean_payload)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def publish(self, id: int, note: str | None = None, pin: bool = False) -> dict:
        found_suggestion = self.repo.session.get(self.Suggestion, int(id))
        if found_suggestion is None: raise HTTPException(404, "La sugerencia solicitada no existe")
        found_suggestion.status = "published"
        found_suggestion.is_public = True
        current_utc_time = dt.datetime.now(dt.timezone.utc)
        found_suggestion.published_at = current_utc_time
        found_suggestion.reviewed_by_id = get_current_user_id()
        if note is not None: found_suggestion.moderation_note = note
        self.repo.session.add(found_suggestion)
        self.repo.session.commit()
        return serialize(found_suggestion)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def reject(self, id: int, note: str) -> dict:
        found_suggestion = self.repo.session.get(self.Suggestion, int(id))
        if found_suggestion is None: raise HTTPException(404, "La sugerencia solicitada no existe")
        found_suggestion.status = "rejected"
        found_suggestion.is_public = False
        found_suggestion.reviewed_by_id = get_current_user_id()
        found_suggestion.moderation_note = note
        self.repo.session.add(found_suggestion)
        self.repo.session.commit()
        return serialize(found_suggestion)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def merge(self, id: int, target_id: int, note: str | None = None) -> dict:
        if int(id) == int(target_id): raise HTTPException(400, "No es posible fusionar un elemento con sí mismo")
        source_suggestion = self.repo.session.get(self.Suggestion, int(id))
        target_suggestion = self.repo.session.get(self.Suggestion, int(target_id))
        if source_suggestion is None or target_suggestion is None: raise HTTPException(404, "Una o ambas sugerencias no fueron encontradas")
        
        merge_note_text = f"Fusionada con #{target_id}. {note or ''}".strip()
        source_suggestion.status = "merged"
        source_suggestion.is_public = False
        source_suggestion.moderation_note = merge_note_text
        self.repo.session.add(source_suggestion)
        self.repo.session.commit()
        return serialize(source_suggestion)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def reopen(self, id: int) -> dict:
        found_suggestion = self.repo.session.get(self.Suggestion, int(id))
        if found_suggestion is None: raise HTTPException(404, "La sugerencia solicitada no fue encontrada")
        found_suggestion.status = "pending"
        found_suggestion.is_public = False
        self.repo.session.add(found_suggestion)
        self.repo.session.commit()
        return serialize(found_suggestion)

class CommentService(BaseService):
    from ..models.feedback import Comment

    def create(self, obj):  # type: ignore[override]
        if not isinstance(obj, dict): return super().create(obj)
        clean_payload = dict(obj)
        clean_payload["status"] = "pending"
        clean_payload["is_public"] = False
        return super().create(clean_payload)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def publish_comment(self, id: int, note: str | None = None) -> dict:
        found_comment = self.repo.session.get(self.Comment, int(id))
        if found_comment is None: raise HTTPException(404, "El comentario solicitado no existe")
        found_comment.status = "published"
        found_comment.is_public = True
        current_utc_time = dt.datetime.now(dt.timezone.utc)
        found_comment.published_at = current_utc_time
        self.repo.session.add(found_comment)
        self.repo.session.commit()
        return serialize(found_comment)

    @exposed_action("write", groups=["feedback_group_moderator", "core_group_superadmin"])
    def reject_comment(self, id: int, note: str | None = None) -> dict:
        found_comment = self.repo.session.get(self.Comment, int(id))
        if found_comment is None: raise HTTPException(404, "El comentario solicitado no existe")
        found_comment.status = "rejected"
        found_comment.is_public = False
        self.repo.session.add(found_comment)
        self.repo.session.commit()
        return serialize(found_comment)