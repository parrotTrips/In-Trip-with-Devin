import pytest

from app.services import admin_service


class _Execute:
    def __init__(self, value=None):
        self.value = value or {}

    def execute(self):
        return self.value


class _Values:
    def __init__(self):
        self.clears = []
        self.updates = []

    def clear(self, *, spreadsheetId, range):
        self.clears.append({"spreadsheetId": spreadsheetId, "range": range})
        return _Execute()

    def update(self, *, spreadsheetId, range, valueInputOption, body):
        self.updates.append({
            "spreadsheetId": spreadsheetId,
            "range": range,
            "valueInputOption": valueInputOption,
            "body": body,
        })
        return _Execute()


class _Spreadsheets:
    def __init__(self, values):
        self._values = values
        self.batch_updates = []

    def values(self):
        return self._values

    def get(self, *, spreadsheetId, fields):
        return _Execute({"sheets": [{"properties": {"title": "Feedbacks"}}]})

    def batchUpdate(self, *, spreadsheetId, body):
        self.batch_updates.append({"spreadsheetId": spreadsheetId, "body": body})
        return _Execute()


class _Sheets:
    def __init__(self):
        self.values_api = _Values()

    def spreadsheets(self):
        return _Spreadsheets(self.values_api)


class _Connection:
    def __init__(self, rows):
        self.rows = rows
        self.closed = False

    async def fetch(self, query, *args):
        assert args == ("trip-feedback-sync",)
        return self.rows

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_admin_sync_feedback_to_sheet_writes_feedback_rows(monkeypatch):
    sheets = _Sheets()
    conn = _Connection([
        {
            "feedback_id": "feedback-1",
            "trip_uuid": "trip-feedback-sync",
            "traveler_name": "Ada Lovelace",
            "phone": "+15550000001",
            "feedback": "Loved the itinerary.",
            "created_at": "2026-08-27T12:00:00+00:00",
        },
        {
            "feedback_id": "feedback-2",
            "trip_uuid": "trip-feedback-sync",
            "traveler_name": "Grace Hopper",
            "phone": "+15550000002",
            "feedback": "More transport details please.",
            "created_at": "2026-08-27T13:00:00+00:00",
        },
    ])

    monkeypatch.setattr(admin_service, "TRIP_CONTENT_SHEET_ID", "sheet-123")
    monkeypatch.setattr(admin_service, "_build_sheets_client_adc", lambda: sheets)

    async def fake_get_connection():
        return conn

    monkeypatch.setattr(admin_service, "_get_connection", fake_get_connection)

    result = await admin_service.admin_sync_feedback_to_sheet("trip-feedback-sync")

    assert result == {"status": "ok", "trip_uuid": "trip-feedback-sync", "feedback_rows": 2}
    assert conn.closed is True
    assert sheets.values_api.clears == [{"spreadsheetId": "sheet-123", "range": "Feedbacks"}]
    assert sheets.values_api.updates == [{
        "spreadsheetId": "sheet-123",
        "range": "Feedbacks!A1",
        "valueInputOption": "RAW",
        "body": {
            "values": [
                ["feedback_id", "trip_uuid", "traveler_name", "phone", "feedback", "created_at"],
                ["feedback-1", "trip-feedback-sync", "Ada Lovelace", "+15550000001", "Loved the itinerary.", "2026-08-27T12:00:00+00:00"],
                ["feedback-2", "trip-feedback-sync", "Grace Hopper", "+15550000002", "More transport details please.", "2026-08-27T13:00:00+00:00"],
            ]
        },
    }]
