"""Tests unitarios para PracticeChecklistService (acciones close, reopen)."""
from __future__ import annotations

import datetime as dt
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from .conftest import FakeChecklist


class TestClose:
    """Acción close: cierra un checklist y actualiza campos."""

    def test_close_sets_status_closed(self, checklist_service, mock_session):
        rec = FakeChecklist(status="open")
        mock_session.get.return_value = rec

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={"id": 1}):
            result = checklist_service.close(id=1)

        assert rec.status == "closed"
        assert rec.closed_at is not None
        mock_session.commit.assert_called_once()

    def test_close_sets_is_public_when_requested(self, checklist_service, mock_session):
        rec = FakeChecklist(status="open", is_public=False)
        mock_session.get.return_value = rec

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            checklist_service.close(id=1, make_public=True)

        assert rec.is_public is True

    def test_close_appends_note_to_description(self, checklist_service, mock_session):
        rec = FakeChecklist(description="Desc original")
        mock_session.get.return_value = rec

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            checklist_service.close(id=1, close_note="Motivo de cierre")

        assert "[Cierre] Motivo de cierre" in rec.description
        assert "Desc original" in rec.description

    def test_close_note_on_empty_description(self, checklist_service, mock_session):
        rec = FakeChecklist(description=None)
        mock_session.get.return_value = rec

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            checklist_service.close(id=1, close_note="Nota")

        assert rec.description == "[Cierre] Nota"

    def test_close_without_note_keeps_description(self, checklist_service, mock_session):
        rec = FakeChecklist(description="Intacta")
        mock_session.get.return_value = rec

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            checklist_service.close(id=1)

        assert rec.description == "Intacta"

    def test_close_sets_closed_at_utc(self, checklist_service, mock_session):
        rec = FakeChecklist()
        mock_session.get.return_value = rec

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            checklist_service.close(id=1)

        assert rec.closed_at.tzinfo == dt.timezone.utc

    def test_close_not_found_raises_404(self, checklist_service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            checklist_service.close(id=999)
        assert exc_info.value.status_code == 404


class TestReopen:
    """Acción reopen: reabre un checklist cerrado."""

    def test_reopen_sets_status_open(self, checklist_service, mock_session):
        rec = FakeChecklist(status="closed", closed_at=dt.datetime.now(dt.timezone.utc))
        mock_session.get.return_value = rec

        with patch("modules.practice_checklist.services.checklist.serialize", return_value={}):
            checklist_service.reopen(id=1)

        assert rec.status == "open"
        assert rec.closed_at is None
        mock_session.commit.assert_called_once()

    def test_reopen_not_found_raises_404(self, checklist_service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            checklist_service.reopen(id=999)
        assert exc_info.value.status_code == 404
