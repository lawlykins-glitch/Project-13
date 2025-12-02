#Lawkins
#12/02/2025
#Project12

from business import Region, DATE_FORMAT
from datetime import date, datetime

"""
This module contains functions for getting
sales data from a user.
"""

def get_amount() -> float:
    """
    Gets a sales amount greater than zero from the user,
    converts it to a float value, and returns the float
    value.
    """
    while True:
        try:
            amount = float(input(f"{'Amount:':20}"))
        except ValueError:
            print("Invalid amount value.\n")
            continue
            
        if amount > 0:
            return amount
        else:
            print("Amount must be greater than zero.\n")

def get_month() -> int:
    """
    Gets a month between 1 and 12 from the user, converts
    it to an int value, and returns the int value.
    """
    while True:
        try:
            month = int(input(f"{'Month (1-12):':20}"))
        except ValueError:
            print("Invalid month value.\n")
            continue
        
        if month >= 1 and month <= 12:
            return month
        else:
            print("Month must be between 1 and 12.\n")

def get_day(month:int) -> int:
    """
    Gets a day from the user, converts it to an int
    value, and returns the int value. Based on month
    parameter, day must be between 1 and 28, 30, or 31.
    """
    if month == 2:
        max_day = 28
    elif month == 4 or month == 6 or month == 9 or month == 11:
        max_day = 30
    else:
        max_day = 31

    while True:
        try:
            prompt = f"Day (1-{max_day}):"
            day = int(input(f"{prompt:20}"))
        except ValueError:
            print("Invalid day value.\n")
            continue
        
        if day >= 1 and day <= max_day:    
            return day
        else:
            print(f"Day must be between 1 and {max_day}.\n")

def get_year() -> int:
    """
    Gets a year between 2000 and 9999 from the user,
    converts it to an int value, and returns the int value.
    """
    while True:
        try:
            year = int(input(f"{'Year:':20}"))
        except ValueError:
            print("Invalid year value.\n")
            continue
        
        if year >= 2000 and year <= 9999:
            return year
        else:
            print("Year must be between 2000 and 9999.\n")

def get_region(regions) -> Region:
    """
    Gets a valid region code from the user and returns a Region object.
    """
    while True:
        code = input(f"{'Region:':20}")
        region = regions.get(code)
        if region == None:
            print(f"Region must be one of the following: {regions}.\n")
        else:
            return region   

def get_date() -> date:
    """
    Gets a date with a year between 2000 and 9999
    from the user and returns a date object.
    """
    while True:
        date_str = input(f"{'Date (yyyy-mm-dd)':20}")
        try:
            sales_date = datetime.strptime(date_str, DATE_FORMAT)
            # return a date object rather than a datetime object
            return date(sales_date.year, sales_date.month, sales_date.day)
        except ValueError:
            print("Date must be valid and in 'yyyy-mm-dd' format.\n")
            continue

        if sales_date.year >= 2000 and sales_date.year <= 9999:
            return sales_date
        else:
            print("Year must be between 2000 and 9999.\n")








    
