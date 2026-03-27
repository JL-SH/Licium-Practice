import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from modules.feedback_moderation.models.feedback import Suggestion
from modules.feedback_moderation.services.feedback import SuggestionService

@pytest.fixture
def mock_service():
    """Prepara una instancia del servicio con dependencias simuladas para los tests"""
    # Construimos el servicio omitiendo la inicialización real del BaseService
    suggestion_service = SuggestionService(MagicMock())
    # Reemplazamos el repositorio y la sesión por objetos simulados
    suggestion_service.repo = MagicMock()
    suggestion_service.repo.session = MagicMock()
    return suggestion_service

@patch("app.core.base.BaseService.create")
def test_initial_state_is_pending_and_private(mock_super_create, mock_service):
    """Prueba que la creación fuerza el estado a 'pending' e 'is_public=False' independientemente del input."""
    # Configuramos el mock para que retorne directamente el diccionario recibido
    mock_super_create.side_effect = lambda x: x

    incoming_payload = {
        "title": "Añadir modo oscuro",
        "content": "Sería genial para la vista.",
        "is_public": True  # Intento de forzar visibilidad desde el exterior
    }
    
    operation_result = mock_service.create(incoming_payload)
    
    assert operation_result["status"] == "pending", "El estado inicial debe ser siempre pending"
    assert operation_result["is_public"] is False, "El registro debe crearse como privado obligatoriamente"
    mock_super_create.assert_called_once()

@patch("modules.feedback_moderation.services.feedback.get_current_user_id")
@patch("modules.feedback_moderation.services.feedback.serialize")
def test_publish_transition_makes_it_public(mock_serialize, mock_get_user, mock_service):
    """Prueba que al publicar una sugerencia, esta se vuelve pública y su estado cambia correctamente."""
    # Configuramos el identificador del moderador simulado
    mock_get_user.return_value = "uuid-del-moderador"

    simulated_suggestion = Suggestion(id=1, status="pending", is_public=False)
    mock_service.repo.session.get.return_value = simulated_suggestion
    
    mock_serialize.side_effect = lambda obj: {"status": obj.status, "is_public": obj.is_public, "moderation_note": obj.moderation_note}
    
    operation_result = mock_service.publish(id=1, note="Aprobado por moderación")
    
    assert operation_result["status"] == "published"
    assert operation_result["is_public"] is True
    assert operation_result["moderation_note"] == "Aprobado por moderación"
    mock_service.repo.session.commit.assert_called_once()

@patch("modules.feedback_moderation.services.feedback.get_current_user_id")
@patch("modules.feedback_moderation.services.feedback.serialize")
def test_reject_transition_keeps_it_private(mock_serialize, mock_get_user, mock_service):
    """Prueba que al rechazar una sugerencia, esta permanece privada y su estado refleja el rechazo."""
    mock_get_user.return_value = "uuid-del-moderador"
    simulated_suggestion = Suggestion(id=2, status="pending", is_public=False)
    mock_service.repo.session.get.return_value = simulated_suggestion
    mock_serialize.side_effect = lambda obj: {"status": obj.status, "is_public": obj.is_public, "moderation_note": obj.moderation_note}
    
    operation_result = mock_service.reject(id=2, note="No es viable")
    
    assert operation_result["status"] == "rejected"
    assert operation_result["is_public"] is False
    assert operation_result["moderation_note"] == "No es viable"
    mock_service.repo.session.commit.assert_called_once()

def test_merge_fails_if_target_is_same_as_source(mock_service):
    """Prueba que la validación de negocio impide fusionar una sugerencia consigo misma."""
    with pytest.raises(HTTPException) as raised_exception:
        mock_service.merge(id=5, target_id=5, note="Merge loop")
        
    assert raised_exception.value.status_code == 400
    assert "No es posible fusionar un elemento con sí mismo" in raised_exception.value.detail