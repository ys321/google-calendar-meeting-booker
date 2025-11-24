from __future__ import annotations

from typing import List
import datetime
from dateutil import parser as date_parser
from dateutil import tz as dateutil_tz

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from calendar_tools import list_events, create_event, simplify_events
from config import GEMINI_MODEL_NAME, DEFAULT_TIMEZONE, GOOGLE_API_KEY, CALENDAR_ID


# ------------- LangChain Tools -------------


@tool("check_availability", return_direct=False)
def check_availability_tool(start_iso: str, end_iso: str) -> str:
    """
    Check existing events between 'start_iso' and 'end_iso' (ISO8601 strings).
    Returns a JSON-like string of busy events. The LLM should infer free slots.
    """
    events = list_events(start_iso, end_iso)
    simplified = simplify_events(events)
    return str(simplified)


@tool("create_meeting", return_direct=False)
def create_meeting_tool(
    title: str = "Initial Call with Vaidrix Team",
    start_iso: str = "",
    end_iso: str = "",
    attendees: str = "",
    description: str = "",
    location: str = "",
) -> str:
    """
    Create a meeting in the shared Google Calendar.

    - title: title/subject for the event (default: "Initial Call with Vaidrix Team")
    - start_iso: start time (ISO 8601 with timezone) - REQUIRED
    - end_iso: end time (ISO 8601 with timezone) - REQUIRED
    - attendees: comma-separated list of attendee email addresses
    - description: optional description for the event
    - location: optional location or meeting link
    """
    # Validate that start_iso is provided
    if not start_iso or not start_iso.strip():
        return "Error: Start time (start_iso) is required to create a meeting."
    
    # Validate that the meeting is in the future
    try:
        # Parse ISO 8601 datetime string using dateutil (handles various formats)
        start_datetime = date_parser.parse(start_iso)
        
        # Get current time in UTC for comparison
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        
        # Convert start_datetime to UTC if it has timezone info
        if start_datetime.tzinfo:
            start_utc = start_datetime.astimezone(datetime.timezone.utc)
        else:
            # If no timezone, assume it's in the default timezone and convert to UTC
            default_tz = dateutil_tz.gettz(DEFAULT_TIMEZONE)
            if default_tz:
                start_datetime = start_datetime.replace(tzinfo=default_tz)
                start_utc = start_datetime.astimezone(datetime.timezone.utc)
            else:
                # Fallback: treat as UTC
                start_utc = start_datetime.replace(tzinfo=datetime.timezone.utc)
        
        # Add a 1-minute buffer to account for clock skew and parsing differences
        # This ensures we don't reject valid future times due to minor timing issues
        buffer = datetime.timedelta(minutes=1)
        
        if start_utc <= (now_utc + buffer):
            # Calculate time difference for better error message
            time_diff = start_utc - now_utc
            hours = int(time_diff.total_seconds() / 3600)
            minutes = int((time_diff.total_seconds() % 3600) / 60)
            
            if time_diff.total_seconds() < 0:
                # Date is in the past - provide helpful error for LLM to recalculate
                return f"Error: Cannot book a meeting in the past. The requested start time ({start_iso}) parsed to {start_utc.isoformat()} UTC, which is {abs(hours)} hours and {abs(minutes)} minutes in the past. Current time is {now_utc.isoformat()} UTC. Please recalculate the date - if the user said 'tomorrow', ensure you're using the correct future date (current date + 1 day)."
            else:
                # Very close to now (within 1 minute) - still reject to be safe
                return f"Error: The requested start time ({start_iso}) is too close to the current time. Please book at least a few minutes in advance. Current time: {now_utc.isoformat()} UTC."
    except (ValueError, TypeError, AttributeError) as e:
        return f"Error: Invalid date format for start_iso: {start_iso}. Error: {str(e)}. Please provide a valid ISO 8601 datetime string."
    
    # Use default title if not provided or empty
    if not title or title.strip() == "":
        title = "Initial Call with Vaidrix Team"
    
    attendees_emails: List[str] = [
        e.strip() for e in attendees.split(",") if e.strip()
    ]

    event = create_event(
        summary=title,
        start_iso=start_iso,
        end_iso=end_iso,
        attendees_emails=attendees_emails,
        description=description,
        location=location or None,
    )
    link = event.get("htmlLink")
    
    # Extract Google Meet link from conference data
    # Check multiple possible locations for the Meet link
    meet_link = ""
    
    # Method 1: Check conferenceData.entryPoints (most common)
    if event.get("conferenceData") and event["conferenceData"].get("entryPoints"):
        for entry_point in event["conferenceData"]["entryPoints"]:
            if entry_point.get("entryPointType") == "video":
                meet_link = entry_point.get("uri", "")
                break
    
    # Method 2: Check hangoutLink field (legacy/alternative)
    if not meet_link and event.get("hangoutLink"):
        meet_link = event.get("hangoutLink")
    
    # Method 3: Check conferenceData.conferenceId and construct link
    if not meet_link and event.get("conferenceData") and event["conferenceData"].get("conferenceId"):
        # Sometimes the link is in the conference solution
        conf_data = event["conferenceData"]
        if conf_data.get("conferenceSolution") and conf_data["conferenceSolution"].get("uri"):
            meet_link = conf_data["conferenceSolution"]["uri"]
    
    # Method 4: Check if there's a location field with meet link
    if not meet_link and event.get("location"):
        location = event.get("location", "")
        if "meet.google.com" in location or "hangouts.google.com" in location:
            meet_link = location
    
    # Build response message
    response_parts = ["OK. I have booked the meeting.\n\nHere are the details:\n"]
    response_parts.append(f"- **Title**: {title}\n")
    
    # Format date and time nicely
    try:
        start_dt = date_parser.parse(start_iso)
        end_dt = date_parser.parse(end_iso)
        date_str = start_dt.strftime("%B %d, %Y")
        time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')} ({DEFAULT_TIMEZONE})"
        response_parts.append(f"- **Date**: {date_str}\n")
        response_parts.append(f"- **Time**: {time_str}\n")
    except:
        response_parts.append(f"- **Start**: {start_iso}\n")
        response_parts.append(f"- **End**: {end_iso}\n")
    
    if attendees_emails:
        response_parts.append(f"- **Attendees**: {', '.join(attendees_emails)}\n")
    
    response_parts.append(f"- **Calendar Link**: [{link}]({link})\n")
    
    if meet_link:
        response_parts.append(f"- **Google Meet Link**: [{meet_link}]({meet_link})\n")
    else:
        response_parts.append(f"- **Google Meet Link**: The meeting link will be available in your Google Calendar. Please check the calendar event for the video conferencing link.\n")
    
    return "".join(response_parts)


# ------------- Agent Factory -------------


def build_agent():
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please set it with: $env:GOOGLE_API_KEY='your-api-key'"
        )
    
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
    )

    tools = [check_availability_tool, create_meeting_tool]

    # Get current date/time for the system prompt
    now = datetime.datetime.now()
    default_tz = dateutil_tz.gettz(DEFAULT_TIMEZONE)
    if default_tz:
        now_local = now.astimezone(default_tz)
    else:
        now_local = now.replace(tzinfo=datetime.timezone.utc)
    
    current_date_str = now_local.strftime("%Y-%m-%d")
    current_datetime_str = now_local.strftime("%Y-%m-%d %H:%M:%S %Z")
    current_iso = now_local.isoformat()

    system_prompt = f"""You are a helpful meeting booking assistant for Vaidrix.

- You talk in a friendly, professional tone.
- You help users book calls into a shared Google Calendar.
- The business timezone is {DEFAULT_TIMEZONE}. If the user mentions a time without a timezone,
  assume it is in this timezone.
- CURRENT DATE AND TIME (use this as your reference for relative dates):
  - Current date: {current_date_str}
  - Current date and time ({DEFAULT_TIMEZONE}): {current_datetime_str}
  - Current ISO 8601: {current_iso}
- IMPORTANT DATE INTERPRETATION:
  - "tomorrow" means the day after {current_date_str} (i.e., {current_date_str} + 1 day)
  - "today" means {current_date_str}
  - Always use the CURRENT DATE ({current_date_str}) as your reference point when interpreting relative dates
  - When converting relative dates to ISO 8601 format, ensure you're using the correct future date
- Always clarify when the date or time is ambiguous.
- CRITICAL: The create_meeting tool will automatically reject past dates, so you should trust the tool's validation.
  If the tool says a date is in the past, it means there was an error in date interpretation - recalculate using the current date ({current_date_str}) as reference.
- The default meeting title is "Initial Call with Vaidrix Team" - use this title unless the user specifies a different title.
- Do NOT ask the user for the meeting title - always use "Initial Call with Vaidrix Team" as the default.
- Before calling create_meeting, make sure:
    1. You have a clear date and time (with duration).
    2. You've correctly interpreted relative dates (e.g., "tomorrow" = {current_date_str} + 1 day = the next day).
    3. You know the attendee email(s) of the client.
    4. Use "Initial Call with Vaidrix Team" as the title (unless user specifies otherwise).
- When the user gives you their email, use it as the attendee email.
- When suggesting slots, check availability with check_availability first.
- After you successfully book a meeting, clearly confirm:
    - date
    - time
    - timezone
    - who will attend
    - Google Calendar link
    - Google Meet video conferencing link (automatically included in all meetings)
- All meetings automatically include a Google Meet video conferencing link for virtual meetings.
- The calendar will be automatically shared with attendees so they can see the meeting. If they can't see it, they should check their Google Calendar for a shared calendar or accept any calendar sharing invitations.
"""

    # Create the agent using the new API
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent
