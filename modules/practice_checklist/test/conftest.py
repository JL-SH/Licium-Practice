"""Fixtures compartidos para tests del módulo practice_checklist."""
from __future__ import annotations

import datetime as dt
from unittest.mock import MagicMock, patch

import pytest


class FakeChecklist:
    """Simula una instancia de PracticeChecklist en memoria."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("name", "Test checklist")
        self.description = kwargs.get("description", "")
        self.status = kwargs.get("status", "open")
        self.is_public = kwargs.get("is_public", False)
        self.owner_id = kwargs.get("owner_id", None)
        self.closed_at = kwargs.get("closed_at", None)


class FakeChecklistItem:
    """Simula una instancia de PracticeChecklistItem en memoria."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.checklist_id = kwargs.get("checklist_id", 1)
        self.title = kwargs.get("title", "Test item")
        self.note = kwargs.get("note", "")
        self.assigned_user_id = kwargs.get("assigned_user_id", None)
        self.is_done = kwargs.get("is_done", False)
        self.done_at = kwargs.get("done_at", None)


@pytest.fixture()
def mock_session():
    """Devuelve un MagicMock que simula repo.session (SQLAlchemy Session)."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture()
def checklist_service(mock_session):
    """Instancia de PracticeChecklistService con session mockeada."""
    from ..services.checklist import PracticeChecklistService

    svc = object.__new__(PracticeChecklistService)
    svc.repo = MagicMock()
    svc.repo.session = mock_session
    return svc


@pytest.fixture()
def item_service(mock_session):
    """Instancia de PracticeChecklistItemService con session mockeada."""
    from ..services.checklist import PracticeChecklistItemService

    svc = object.__new__(PracticeChecklistItemService)
    svc.repo = MagicMock()
    svc.repo.session = mock_session
    return svc
