"""Tests unitarios para PracticeChecklistItemService (acción set_done)."""
from __future__ import annotations

import datetime as dt
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from .conftest import FakeChecklistItem


class TestSetDone:
    """Acción set_done: marca/desmarca ítems como completados."""

    def test_set_done_marks_item_done(self, item_service, mock_session):
        item = FakeChecklistItem(is_done=False)
        mock_session.get.return_value = item

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={"id": 1}):
            item_service.set_done(id=1, done=True)

        assert item.is_done is True
        assert item.done_at is not None
        assert item.done_at.tzinfo == dt.timezone.utc
        mock_session.commit.assert_called_once()

    def test_set_done_marks_item_pending(self, item_service, mock_session):
        item = FakeChecklistItem(is_done=True, done_at=dt.datetime.now(dt.timezone.utc))
        mock_session.get.return_value = item

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            item_service.set_done(id=1, done=False)

        assert item.is_done is False
        assert item.done_at is None

    def test_set_done_default_is_true(self, item_service, mock_session):
        item = FakeChecklistItem(is_done=False)
        mock_session.get.return_value = item

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            item_service.set_done(id=1)

        assert item.is_done is True

    def test_set_done_appends_note(self, item_service, mock_session):
        item = FakeChecklistItem(note="Nota previa")
        mock_session.get.return_value = item

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            item_service.set_done(id=1, note="Completado por revisión")

        assert "[Estado] Completado por revisión" in item.note
        assert "Nota previa" in item.note

    def test_set_done_note_on_empty(self, item_service, mock_session):
        item = FakeChecklistItem(note=None)
        mock_session.get.return_value = item

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            item_service.set_done(id=1, note="Primera nota")

        assert item.note == "[Estado] Primera nota"

    def test_set_done_without_note_keeps_note(self, item_service, mock_session):
        item = FakeChecklistItem(note="Intacta")
        mock_session.get.return_value = item

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            item_service.set_done(id=1)

        assert item.note == "Intacta"

    def test_set_done_not_found_raises_404(self, item_service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            item_service.set_done(id=999)
        assert exc_info.value.status_code == 404
