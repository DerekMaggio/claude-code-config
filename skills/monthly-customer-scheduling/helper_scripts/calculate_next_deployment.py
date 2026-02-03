import calendar
import sys
from datetime import datetime, date

# Convert ordinal words to numbers
ORDINAL_MAP = {
    "first": 1, "1st": 1,
    "second": 2, "2nd": 2,
    "third": 3, "3rd": 3,
    "fourth": 4, "4th": 4,
    "fifth": 5, "5th": 5,
}

def parse_nth(nth):
    """Convert ordinal word or number to integer."""
    if isinstance(nth, int):
        return nth
    nth_lower = str(nth).lower().strip()
    if nth_lower in ORDINAL_MAP:
        return ORDINAL_MAP[nth_lower]
    try:
        return int(nth)
    except ValueError:
        return None

def get_nth_weekday(nth, weekday_name, month_name, year):
    try:
        # Convert ordinal to number
        nth_num = parse_nth(nth)
        if nth_num is None:
            return f"Error: Invalid week number '{nth}'. Use 1-5 or First/Second/Third/Fourth/Fifth."

        # Parse Month Name (handles "March", "mar", "MAR", etc.)
        month_dt = datetime.strptime(month_name, '%B') if len(month_name) > 3 else datetime.strptime(month_name, '%b')
        month = month_dt.month

        # Convert Weekday Name to index (0=Mon, 6=Sun)
        days = {d: i for i, d in enumerate(calendar.day_name)}
        target_day_index = days.get(weekday_name.capitalize())

        if target_day_index is None:
            return "Error: Invalid weekday name."

        # Get the month grid
        month_cal = calendar.monthcalendar(year, month)

        # Filter out the 0s (days not in this month) for that column
        occurrences = [week[target_day_index] for week in month_cal if week[target_day_index] != 0]

        day_of_month = occurrences[nth_num - 1]
        return date(year, month, day_of_month).strftime("%A, %B %d, %Y")

    except ValueError:
        return f"Error: Could not parse '{month_name}' as a month."
    except IndexError:
        return f"Error: There is no {nth} {weekday_name} in {month_name} {year}."

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 calculate_next_deployment.py [N] [Weekday] [Month] [Year]")
        print("  N: Week number (1-5) or ordinal (First, Second, Third, Fourth, Fifth)")
        print("  Example: python3 calculate_next_deployment.py Third Wednesday March 2026")
    else:
        print(get_nth_weekday(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])))