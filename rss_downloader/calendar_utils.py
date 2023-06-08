import datetime
from typing import List


def create_date_list() -> List[datetime.date]:
    """
    Create a list of dates for the next 7 days.

    Returns:
        List: A list of date objects representing the next 7 days.
    """

    today = datetime.date.today()
    date_list = [today + datetime.timedelta(days=i) for i in range(7)]
    return date_list
