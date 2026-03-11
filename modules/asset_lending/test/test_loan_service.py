"""Tests unitarios para AssetLoanService (checkout via create y return_asset)."""
from __future__ import annotations

import datetime as dt
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException

from .conftest import FakeAsset, FakeLoan


class TestCheckout:
    """Checkout: crear un préstamo valida disponibilidad y marca asset como loaned."""

    def test_checkout_marks_asset_loaned(self, loan_service, mock_session):
        asset = FakeAsset(id=1, status="available")
        mock_session.get.return_value = asset

        with patch.object(type(loan_service), "create", wraps=loan_service.create):
            with patch("modules.asset_lending.services.lending.BaseService.create", return_value={"id": 1}):
                result = loan_service.create({
                    "asset_id": 1,
                    "borrower_user_id": 10,
                    "due_at": "2026-03-20T15:00:00+00:00",
                })

        assert asset.status == "loaned"
        mock_session.add.assert_called_with(asset)

    def test_checkout_rejects_loaned_asset(self, loan_service, mock_session):
        asset = FakeAsset(id=1, status="loaned")
        mock_session.get.return_value = asset

        with pytest.raises(HTTPException) as exc_info:
            loan_service.create({
                "asset_id": 1,
                "borrower_user_id": 10,
                "due_at": "2026-03-20T15:00:00+00:00",
            })
        assert exc_info.value.status_code == 400

    def test_checkout_rejects_maintenance_asset(self, loan_service, mock_session):
        asset = FakeAsset(id=1, status="maintenance")
        mock_session.get.return_value = asset

        with pytest.raises(HTTPException) as exc_info:
            loan_service.create({
                "asset_id": 1,
                "borrower_user_id": 10,
                "due_at": "2026-03-20T15:00:00+00:00",
            })
        assert exc_info.value.status_code == 400

    def test_checkout_asset_not_found(self, loan_service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            loan_service.create({
                "asset_id": 999,
                "borrower_user_id": 10,
                "due_at": "2026-03-20T15:00:00+00:00",
            })
        assert exc_info.value.status_code == 404

    def test_checkout_requires_asset_id(self, loan_service, mock_session):
        with pytest.raises(HTTPException) as exc_info:
            loan_service.create({
                "borrower_user_id": 10,
                "due_at": "2026-03-20T15:00:00+00:00",
            })
        assert exc_info.value.status_code == 400

    def test_checkout_parses_dd_mm_yyyy(self, loan_service, mock_session):
        asset = FakeAsset(id=1, status="available")
        mock_session.get.return_value = asset

        payload = {
            "asset_id": 1,
            "borrower_user_id": 10,
            "due_at": "20/03/2026",
        }

        with patch("modules.asset_lending.services.lending.BaseService.create", return_value={"id": 1}) as mock_create:
            loan_service.create(payload)

        created_payload = mock_create.call_args[0][0]
        assert isinstance(created_payload["due_at"], dt.datetime)
        assert created_payload["due_at"].tzinfo == dt.timezone.utc

    def test_checkout_injects_status_and_checkout_at(self, loan_service, mock_session):
        asset = FakeAsset(id=1, status="available")
        mock_session.get.return_value = asset

        with patch("modules.asset_lending.services.lending.BaseService.create", return_value={"id": 1}) as mock_create:
            loan_service.create({
                "asset_id": 1,
                "borrower_user_id": 10,
                "due_at": "2026-03-20T15:00:00+00:00",
            })

        created_payload = mock_create.call_args[0][0]
        assert created_payload["status"] == "open"
        assert created_payload["checkout_at"] is not None
        assert created_payload["checkout_at"].tzinfo == dt.timezone.utc


class TestReturnAsset:
    """return_asset: devuelve un recurso y marca loan como returned."""

    def test_return_marks_loan_returned(self, loan_service, mock_session):
        loan = FakeLoan(id=1, status="open", asset_id=1)
        asset = FakeAsset(id=1, status="loaned")

        def get_side_effect(model, pk):
            from ..models.lending import Loan as LoanModel, Asset as AssetModel
            if model is LoanModel:
                return loan
            if model is AssetModel:
                return asset
            return None

        mock_session.get.side_effect = get_side_effect

        with patch("modules.asset_lending.services.lending.serialize", return_value={"id": 1}):
            loan_service.return_asset(id=1)

        assert loan.status == "returned"
        assert loan.returned_at is not None
        assert asset.status == "available"
        mock_session.commit.assert_called_once()

    def test_return_fails_if_not_open(self, loan_service, mock_session):
        loan = FakeLoan(id=1, status="returned")
        mock_session.get.return_value = loan

        with pytest.raises(HTTPException) as exc_info:
            loan_service.return_asset(id=1)
        assert exc_info.value.status_code == 400

    def test_return_loan_not_found(self, loan_service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            loan_service.return_asset(id=999)
        assert exc_info.value.status_code == 404

    def test_return_sets_note(self, loan_service, mock_session):
        loan = FakeLoan(id=1, status="open", asset_id=1)
        asset = FakeAsset(id=1, status="loaned")

        def get_side_effect(model, pk):
            from ..models.lending import Loan as LoanModel, Asset as AssetModel
            if model is LoanModel:
                return loan
            if model is AssetModel:
                return asset
            return None

        mock_session.get.side_effect = get_side_effect

        with patch("modules.asset_lending.services.lending.serialize", return_value={"id": 1}):
            loan_service.return_asset(id=1, note="Sin daños")

        assert loan.return_note == "Sin daños"

    def test_return_sets_returned_at_utc(self, loan_service, mock_session):
        loan = FakeLoan(id=1, status="open", asset_id=1)
        asset = FakeAsset(id=1, status="loaned")

        def get_side_effect(model, pk):
            from ..models.lending import Loan as LoanModel, Asset as AssetModel
            if model is LoanModel:
                return loan
            if model is AssetModel:
                return asset
            return None

        mock_session.get.side_effect = get_side_effect

        with patch("modules.asset_lending.services.lending.serialize", return_value={"id": 1}):
            loan_service.return_asset(id=1)

        assert loan.returned_at.tzinfo == dt.timezone.utc


class TestMarkMaintenance:
    """mark_maintenance: pasa un recurso a mantenimiento."""

    def test_mark_maintenance_sets_status(self, asset_service, mock_session):
        asset = FakeAsset(id=1, status="available")
        mock_session.get.return_value = asset

        with patch("modules.asset_lending.services.lending.serialize", return_value={"id": 1}):
            asset_service.mark_maintenance(id=1)

        assert asset.status == "maintenance"
        mock_session.commit.assert_called_once()

    def test_mark_maintenance_appends_note(self, asset_service, mock_session):
        asset = FakeAsset(id=1, status="available", notes="Nota previa")
        mock_session.get.return_value = asset

        with patch("modules.asset_lending.services.lending.serialize", return_value={"id": 1}):
            asset_service.mark_maintenance(id=1, note="Teclado roto")

        assert "[Mantenimiento] Teclado roto" in asset.notes
        assert "Nota previa" in asset.notes

    def test_mark_maintenance_not_found(self, asset_service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            asset_service.mark_maintenance(id=999)
        assert exc_info.value.status_code == 404


class TestReleaseMaintenance:
    """release_maintenance: libera un recurso de mantenimiento."""

    def test_release_sets_available(self, asset_service, mock_session):
        asset = FakeAsset(id=1, status="maintenance")
        mock_session.get.return_value = asset

        with patch("modules.asset_lending.services.lending.serialize", return_value={"id": 1}):
            asset_service.release_maintenance(id=1)

        assert asset.status == "available"
        mock_session.commit.assert_called_once()

    def test_release_fails_if_not_maintenance(self, asset_service, mock_session):
        asset = FakeAsset(id=1, status="available")
        mock_session.get.return_value = asset

        with pytest.raises(HTTPException) as exc_info:
            asset_service.release_maintenance(id=1)
        assert exc_info.value.status_code == 400

    def test_release_not_found(self, asset_service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            asset_service.release_maintenance(id=999)
        assert exc_info.value.status_code == 404
