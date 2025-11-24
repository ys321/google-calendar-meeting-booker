from __future__ import annotations

import uuid
from typing import List, Dict, Any

from googleapiclient.discovery import build

from config import CALENDAR_ID, DEFAULT_TIMEZONE
from google_oauth import load_credentials

def _get_calendar_service():
    creds = load_credentials()
    if not creds:
        # No OAuth token yet – tell developer to visit /auth/google
        raise RuntimeError(
            "Google OAuth credentials not found. "
            "Open http://localhost:5000/auth/google in your browser and authorize."
        )
    service = build("calendar", "v3", credentials=creds)
    return service

def list_events(start_iso: str, end_iso: str) -> List[Dict[str, Any]]:
    """List events in the time range, returned as raw Google event objects."""
    service = _get_calendar_service()
    events_result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])

def create_event(
    summary: str,
    start_iso: str,
    end_iso: str,
    attendees_emails: List[str] | None = None,
    description: str = "",
    location: str | None = None,
) -> Dict[str, Any]:
    """Create a new event with Google Meet and real attendees; return event object."""
    service = _get_calendar_service()

    event_body: Dict[str, Any] = {
        "summary": summary,
        "description": description or "",
        "start": {"dateTime": start_iso, "timeZone": DEFAULT_TIMEZONE},
        "end": {"dateTime": end_iso, "timeZone": DEFAULT_TIMEZONE},
    }

    # Real attendees now allowed with OAuth
    if attendees_emails:
        event_body["attendees"] = [{"email": email} for email in attendees_emails]

    if location:
        event_body["location"] = location

    # Ask Google to create a Meet link
    event_body["conferenceData"] = {
        "createRequest": {
            "requestId": f"meet-{uuid.uuid4().hex[:8]}-{start_iso[:10]}",
            "conferenceSolutionKey": {"type": "hangoutsMeet"},
        }
    }

    # Create event with conferenceDataVersion=1 to actually get the Meet link
    event = (
        service.events()
        .insert(
            calendarId=CALENDAR_ID,
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all",  # send email invites to attendees
        )
        .execute()
    )

    # Sometimes the response may still not show conferenceData fully;
    # fetch it again using conferenceDataVersion=1
    event_id = event.get("id")
    if event_id and not event.get("conferenceData"):
        try:
            event = (
                service.events()
                .get(
                    calendarId=CALENDAR_ID,
                    eventId=event_id,
                    conferenceDataVersion=1,
                )
                .execute()
            )
        except Exception:
            pass

    return event


def simplify_events(events: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Return simplified list for the LLM to understand (summary, start, end)."""
    simplified = []
    for e in events:
        simplified.append(
            {
                "summary": e.get("summary", "(no title)"),
                "start": e.get("start", {}).get(
                    "dateTime", e.get("start", {}).get("date")
                ),
                "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date")),
            }
        )
    return simplified
