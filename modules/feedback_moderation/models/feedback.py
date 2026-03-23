from __future__ import annotations
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UUID, Table, Column
from sqlalchemy.orm import relationship, backref
from app.core.base import Base
from app.core.fields import field

suggestion_tag_rel = Table(
    "feedback_moderation_suggestion_tag_rel",
    Base.metadata,
    Column("suggestion_id", Integer, ForeignKey("feedback_moderation_suggestion.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("feedback_moderation_tag.id", ondelete="CASCADE"), primary_key=True),
    extend_existing = True,
)

class Tag(Base):
    __tablename__ = "feedback_moderation_tag"
    __abstract__ = False
    __model__ = "tag"
    __service__ = "modules.feedback_moderation.services.feedback.TagService"

    name = field(String(100), required=True, public=True, editable=True)
    slug = field(String(100), required=True, public=True, editable=True)
    color = field(String(20), required=False, public=True, editable=True, default="#808080")

class Suggestion(Base):
    __tablename__ = "feedback_moderation_suggestion"
    __abstract__ = False
    __model__ = "suggestion"
    __service__ = "modules.feedback_moderation.services.feedback.SuggestionService"

    title = field(String(200), required=True, public=True, editable=True)
    content = field(Text, required=True, public=True, editable=True)
    status = field(
        String(20), required=True, default="pending", public=True, editable=True,
        info={"choices": [
            {"label": "Pendiente", "value": "pending"},
            {"label": "Publicada", "value": "published"},
            {"label": "Rechazada", "value": "rejected"},
            {"label": "Fusionada", "value": "merged"}
        ]}
    )
    author_email = field(String(150), required=True, public=True, editable=True)
    author_name = field(String(100), required=False, public=True, editable=True)
    is_public = field(Boolean, required=True, default=False, public=True, editable=True)
    moderation_note = field(Text, required=False, public=True, editable=True)
    published_at = field(DateTime(timezone=True), required=False, public=True, editable=False)
    reviewed_by_id = field(UUID, ForeignKey("core_user.id"), required=False, public=True, editable=True)
    
    tags = relationship(
        "modules.feedback_moderation.models.feedback.Tag",
        secondary=suggestion_tag_rel,
        info={"public": True, "editable": True}
    )

class Comment(Base):
    __tablename__ = "feedback_moderation_comment"
    __abstract__ = False
    __model__ = "comment"
    __service__ = "modules.feedback_moderation.services.feedback.CommentService"

    suggestion_id = field(Integer, ForeignKey("feedback_moderation_suggestion.id", ondelete="CASCADE"), required=True, public=True, editable=True)
    content = field(Text, required=True, public=True, editable=True)
    status = field(
        String(20), required=True, default="pending", public=True, editable=True,
        info={"choices": [
            {"label": "Pendiente", "value": "pending"},
            {"label": "Publicado", "value": "published"},
            {"label": "Rechazado", "value": "rejected"}
        ]}
    )
    author_email = field(String(150), required=True, public=True, editable=True)
    is_public = field(Boolean, required=True, default=False, public=True, editable=True)
    published_at = field(DateTime(timezone=True), required=False, public=True, editable=False)