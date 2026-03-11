"""Fixtures compartidos para tests del módulo asset_lending."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class FakeAsset:
    """Simula una instancia de Asset en memoria."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("name", "Portátil Dell")
        self.asset_code = kwargs.get("asset_code", "LAPTOP-001")
        self.status = kwargs.get("status", "available")
        self.location_id = kwargs.get("location_id", 1)
        self.responsible_user_id = kwargs.get("responsible_user_id", None)
        self.notes = kwargs.get("notes", "")


class FakeLoan:
    """Simula una instancia de Loan en memoria."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.asset_id = kwargs.get("asset_id", 1)
        self.borrower_user_id = kwargs.get("borrower_user_id", 10)
        self.checkout_at = kwargs.get("checkout_at", None)
        self.due_at = kwargs.get("due_at", None)
        self.returned_at = kwargs.get("returned_at", None)
        self.status = kwargs.get("status", "open")
        self.checkout_note = kwargs.get("checkout_note", "")
        self.return_note = kwargs.get("return_note", "")


@pytest.fixture()
def mock_session():
    """Devuelve un MagicMock que simula repo.session (SQLAlchemy Session)."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture()
def loan_service(mock_session):
    """Instancia de AssetLoanService con session mockeada."""
    from ..services.lending import AssetLoanService

    svc = object.__new__(AssetLoanService)
    svc.repo = MagicMock()
    svc.repo.session = mock_session
    return svc


@pytest.fixture()
def asset_service(mock_session):
    """Instancia de AssetService con session mockeada."""
    from ..services.lending import AssetService

    svc = object.__new__(AssetService)
    svc.repo = MagicMock()
    svc.repo.session = mock_session
    return svc
