import pytest
import datetime as dt
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from modules.community_events.services.events import EventService, RegistrationService
from modules.community_events.models.events import Event, Registration

@pytest.fixture
def mock_event_service():
    instance = EventService(MagicMock())
    instance.repo = MagicMock()
    instance.repo.session = MagicMock()
    return instance

@pytest.fixture
def mock_registration_service():
    instance = RegistrationService(MagicMock())
    instance.repo = MagicMock()
    instance.repo.session = MagicMock()
    return instance


@patch("modules.community_events.services.events.serialize")
def test_publish_event_changes_status_and_visibility(mock_serialize, mock_event_service):
    event_stub = Event(id=1, status="draft", is_public=False)
    mock_event_service.repo.session.get.return_value = event_stub

    def _serialize_event(obj):
        return {"status": obj.status, "is_public": obj.is_public}

    mock_serialize.side_effect = _serialize_event

    response = mock_event_service.publish_event(id=1)

    assert response["status"] == "published"
    assert response["is_public"] is True
    mock_event_service.repo.session.commit.assert_called_once()


@patch("modules.community_events.services.events.serialize")
def test_cancel_event_hides_it_from_public(mock_serialize, mock_event_service):
    event_stub = Event(id=2, status="published", is_public=True)
    mock_event_service.repo.session.get.return_value = event_stub

    def _serialize_event(obj):
        return {"status": obj.status, "is_public": obj.is_public}

    mock_serialize.side_effect = _serialize_event

    response = mock_event_service.cancel_event(id=2, reason="Lluvia extrema")

    assert response["status"] == "cancelled"
    assert response["is_public"] is False
    mock_event_service.repo.session.commit.assert_called_once()


@patch("modules.community_events.services.events.serialize")
def test_checkin_success_for_confirmed_user(mock_serialize, mock_registration_service):
    reg_stub = Registration(id=10, status="confirmed", checkin_at=None)
    mock_registration_service.repo.session.get.return_value = reg_stub

    def _serialize_reg(obj):
        return {"checkin_at": obj.checkin_at}

    mock_serialize.side_effect = _serialize_reg

    response = mock_registration_service.checkin(id=10, source="scanner")

    assert response["checkin_at"] is not None
    mock_registration_service.repo.session.commit.assert_called_once()


def test_checkin_fails_for_cancelled_user(mock_registration_service):
    reg_stub = Registration(id=11, status="cancelled", checkin_at=None)
    mock_registration_service.repo.session.get.return_value = reg_stub

    with pytest.raises(HTTPException) as raised_exc:
        mock_registration_service.checkin(id=11)

    http_error = raised_exc.value
    assert http_error.status_code == 400
    assert "El estado actual del registro no permite el acceso." in http_error.detail
    mock_registration_service.repo.session.commit.assert_not_called()