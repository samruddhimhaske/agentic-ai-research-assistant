"""
tools/datetime_tool.py - Date and Time Tool
=============================================
This tool provides the agent with current date/time information.

Why is this needed?
  AI language models have a "knowledge cutoff" date — they don't
  know what today's date is unless we tell them. This tool bridges
  that gap by providing real-time date/time information.

The agent uses this tool when the user asks:
  - "What is today's date?"
  - "What day of the week is it?"
  - "How many days until Christmas?"
  - "What time is it right now?"
"""

from datetime import datetime, timezone
import calendar


class DateTimeTool:
    """
    Provides current date and time information to the AI agent.
    
    Usage:
        dt_tool = DateTimeTool()
        result = dt_tool.run("current date and time")
        # Returns formatted date/time info
    """

    # Tool metadata
    name: str = "DateTime"
    description: str = (
        "Provides current date, time, day of week, and other time-related information. "
        "Use this when the user asks about today's date, current time, "
        "day of the week, or any time-sensitive information."
    )

    def run(self, query: str = "current") -> str:
        """
        Return date/time information based on the query.
        
        Args:
            query: What time info is needed (default returns everything)
            
        Returns:
            Formatted string with the requested date/time information
        """
        # Get current date and time
        now = datetime.now()
        now_utc = datetime.now(timezone.utc)

        query_lower = query.lower()

        # --- Handle specific query types ---

        if "time" in query_lower and "date" not in query_lower:
            # User only wants the time
            return self._format_time_only(now)

        elif "date" in query_lower and "time" not in query_lower:
            # User only wants the date
            return self._format_date_only(now)

        elif "day" in query_lower and "week" in query_lower:
            # User wants the day of the week
            return f"Today is {now.strftime('%A')} ({now.strftime('%B %d, %Y')})"

        elif "week" in query_lower and "number" in query_lower:
            # What week number of the year
            week_num = now.isocalendar()[1]
            return f"Current week number: {week_num} of {now.year}"

        elif "month" in query_lower:
            # Info about the current month
            return self._format_month_info(now)

        elif "year" in query_lower:
            # Just the year
            return f"Current year: {now.year}"

        elif "utc" in query_lower or "gmt" in query_lower:
            # UTC time
            return f"Current UTC time: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}"

        else:
            # Default: return comprehensive date/time info
            return self._format_full_datetime(now, now_utc)

    def _format_full_datetime(self, now: datetime, now_utc: datetime) -> str:
        """Return a comprehensive date/time report."""
        # Get all the pieces of information
        day_name = now.strftime("%A")          # e.g. "Monday"
        month_name = now.strftime("%B")        # e.g. "January"
        day_num = now.strftime("%d")           # e.g. "15"
        year = now.strftime("%Y")             # e.g. "2024"
        time_12h = now.strftime("%I:%M %p")   # e.g. "02:30 PM"
        time_24h = now.strftime("%H:%M")      # e.g. "14:30"
        week_num = now.isocalendar()[1]       # e.g. 3

        # Calculate day of the year (e.g. Jan 15 = day 15)
        day_of_year = now.timetuple().tm_yday

        # How many days are left in the year
        days_in_year = 366 if calendar.isleap(now.year) else 365
        days_remaining = days_in_year - day_of_year

        return (
            f"📅 Current Date & Time Information:\n\n"
            f"• Date: {day_name}, {month_name} {day_num}, {year}\n"
            f"• Time: {time_12h} (Local) / {time_24h} (24-hour)\n"
            f"• UTC Time: {now_utc.strftime('%H:%M UTC')}\n"
            f"• Week Number: Week {week_num} of {year}\n"
            f"• Day of Year: Day {day_of_year} of {days_in_year}\n"
            f"• Days Remaining in Year: {days_remaining}\n"
            f"• Leap Year: {'Yes' if calendar.isleap(now.year) else 'No'}"
        )

    def _format_date_only(self, now: datetime) -> str:
        """Return just the date in a friendly format."""
        return (
            f"Today's date: {now.strftime('%A, %B %d, %Y')}\n"
            f"Numeric format: {now.strftime('%Y-%m-%d')}"
        )

    def _format_time_only(self, now: datetime) -> str:
        """Return just the time."""
        return (
            f"Current time: {now.strftime('%I:%M:%S %p')} (local)\n"
            f"24-hour format: {now.strftime('%H:%M:%S')}"
        )

    def _format_month_info(self, now: datetime) -> str:
        """Return information about the current month."""
        month_name = now.strftime("%B")
        year = now.year
        # Get number of days in the current month
        days_in_month = calendar.monthrange(year, now.month)[1]
        days_passed = now.day
        days_left = days_in_month - days_passed

        return (
            f"Current month: {month_name} {year}\n"
            f"• Days in {month_name}: {days_in_month}\n"
            f"• Days passed: {days_passed}\n"
            f"• Days remaining: {days_left}"
        )

    def get_tool_info(self) -> dict:
        """Return tool metadata as a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "example_inputs": [
                "current date and time",
                "what day of the week is it",
                "current month info",
                "what time is it",
                "current UTC time"
            ]
        }
