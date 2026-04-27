import pytest
from unittest.mock import patch, MagicMock
from services.calendar_service import create_calendar_event
from services.exceptions import CalendarServiceError

@pytest.mark.asyncio
async def test_create_calendar_event_unauthorized():
    # Write a test that mocks the build function to simulate an exception
    with patch("services.calendar_service.build") as mock_build:
        mock_build.side_effect = Exception("Invalid credentials")
        
        with pytest.raises(CalendarServiceError) as exc_info:
            await create_calendar_event("Buy milk", {"token": "dummy"})
            
        assert "Invalid credentials" in str(exc_info.value)

@pytest.mark.asyncio
@patch("services.calendar_service.build")
async def test_create_calendar_event_success(mock_build):
    # Mock the calendar service
    mock_service = MagicMock()
    mock_events = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    
    # Setup the mock chain
    mock_build.return_value = mock_service
    mock_service.events.return_value = mock_events
    mock_events.insert.return_value = mock_insert
    mock_execute.return_value = {"id": "event_id_123", "summary": "Buy milk"}
    mock_insert.execute = mock_execute
    
    result = await create_calendar_event("Buy milk", {"token": "dummy"})
    
    assert result == {"id": "event_id_123", "summary": "Buy milk"}
    mock_build.assert_called_once()
    mock_events.insert.assert_called_once()
    args, kwargs = mock_events.insert.call_args
    assert kwargs["calendarId"] == "primary"
    assert kwargs["body"]["summary"] == "Buy milk"
    assert "start" in kwargs["body"]
    assert "end" in kwargs["body"]
