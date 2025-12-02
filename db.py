#Lawkins
#12/02/2025
#Project12

import csv
import os
from pathlib import Path
from business import Region, Regions, DailySales, SalesList, FileImportError

import sqlite3
from contextlib import closing

conn = None

def connect(db_file="sales_db.sqlite", sql_dump="sales_db.sql"):
    """Connect to SQLite; if the DB file is missing but a SQL dump exists, bootstrap it."""
    global conn
    if conn:
        return conn

    script_dir = Path(__file__).resolve().parent
    db_path = script_dir / db_file
    sql_path = script_dir / sql_dump

    needs_bootstrap = (not db_path.exists()) and sql_path.exists()

    conn_obj = sqlite3.connect(db_path)
    conn_obj.row_factory = sqlite3.Row

    if needs_bootstrap:
        sql = sql_path.read_text(encoding='utf-8')
        with conn_obj:
            conn_obj.executescript(sql)
    conn = conn_obj
    return conn

def get_regions():
    query = '''SELECT code, name
               FROM Region'''
    with closing(conn.cursor()) as c:
        c.execute(query)
        rows = c.fetchall()

        regions = Regions()
        for row in rows:
            region = Region(row["code"], row["name"])
            regions.add(region)
        return regions

def get_all_sales():
    try:
        query = '''SELECT ID, amount, salesDate,
                       Region.code, Region.name
                   FROM Sales
                   JOIN Region ON Sales.region = Region.code
                   ORDER BY date(salesDate), region'''
        with closing(conn.cursor()) as c:
            c.execute(query)
            rows = c.fetchall()

            sales = SalesList()
            for row in rows:
                data = DailySales()
                data.fromDb(row)
                sales.add(data)
            return sales
    except sqlite3.OperationalError:
        return None

def _build_filters(start_date=None, end_date=None, region=None):
    """Return a WHERE clause and params for date/region filters."""
    clauses = []
    params = []

    if start_date:
        clauses.append("date(salesDate) >= date(?)")
        params.append(start_date)
    if end_date:
        clauses.append("date(salesDate) <= date(?)")
        params.append(end_date)
    if region:
        clauses.append("region = ?")
        params.append(region)

    where = ""
    if clauses:
        where = " WHERE " + " AND ".join(clauses)
    return where, params

def get_sales_filtered(start_date=None, end_date=None, region=None):
    """Return sales data filtered by optional date range and region."""
    where, params = _build_filters(start_date, end_date, region)
    query = f'''SELECT ID, amount, salesDate,
                       Region.code, Region.name
                FROM Sales
                JOIN Region ON Sales.region = Region.code
                {where}
                ORDER BY date(salesDate), region'''
    with closing(conn.cursor()) as c:
        c.execute(query, params)
        rows = c.fetchall()

        sales = SalesList()
        for row in rows:
            data = DailySales()
            data.fromDb(row)
            sales.add(data)
        return sales

def save_all_sales(sales_list):
    sql = '''INSERT INTO Sales
                (amount, salesDate, region)
             VALUES
                (?, ?, ?)'''
    
    for data in sales_list:
        if data.id == 0:  # if id is zero, it's added sales data
            with closing(conn.cursor()) as c:
                c.execute(sql, (data.amount, data.salesDate, data.region.code))
                conn.commit()

def get_sales(dt, region):
    query = '''SELECT ID, amount, salesDate,
                   Region.code, Region.name
               FROM Sales
               JOIN Region ON Sales.region = Region.code
               WHERE salesDate = ? AND region = ?'''
    with closing(conn.cursor()) as c:
        c.execute(query, (dt, region))
        row = c.fetchone()

        if row:
            data = DailySales()
            data.fromDb(row)
            return data
        else:
            return None

def update_sales_amount(data):
    sql = '''UPDATE Sales
             SET amount = ?
             WHERE ID = ?'''
    
    with closing(conn.cursor()) as c:
        c.execute(sql, (data.amount, data.id))
        conn.commit()

def get_sales_summary(start_date=None, end_date=None, region=None):
    """Return aggregate metrics for a date/region slice."""
    where, params = _build_filters(start_date, end_date, region)

    base = f"FROM Sales {where}"
    totals_sql = f'''SELECT COUNT(*) AS count,
                            COALESCE(SUM(amount), 0) AS total,
                            AVG(amount) AS average
                     {base}'''

    region_sql = f'''SELECT Region.code, Region.name,
                            SUM(amount) AS total,
                            COUNT(*) AS count
                     FROM Sales
                     JOIN Region ON Sales.region = Region.code
                     {where}
                     GROUP BY Region.code, Region.name
                     ORDER BY Region.code'''

    quarter_sql = f'''SELECT CASE
                            WHEN CAST(strftime('%m', salesDate) AS INTEGER) BETWEEN 1 AND 3 THEN 1
                            WHEN CAST(strftime('%m', salesDate) AS INTEGER) BETWEEN 4 AND 6 THEN 2
                            WHEN CAST(strftime('%m', salesDate) AS INTEGER) BETWEEN 7 AND 9 THEN 3
                            ELSE 4 END AS quarter,
                            SUM(amount) AS total
                     {base}
                     GROUP BY quarter
                     ORDER BY quarter'''

    top_day_sql = f'''SELECT salesDate, SUM(amount) AS total
                      {base}
                      GROUP BY salesDate
                      ORDER BY total DESC
                      LIMIT 1'''

    with closing(conn.cursor()) as c:
        # totals
        c.execute(totals_sql, params)
        totals = c.fetchone()

        # by region
        c.execute(region_sql, params)
        regions = c.fetchall()

        # by quarter
        c.execute(quarter_sql, params)
        quarters = c.fetchall()

        # top day
        c.execute(top_day_sql, params)
        top_day = c.fetchone()

        return {
            "count": totals["count"] if totals else 0,
            "total": totals["total"] if totals else 0,
            "average": totals["average"] if totals else 0,
            "regions": regions,
            "quarters": quarters,
            "top_day": top_day
        }
    

def already_imported(filename):
    try:
        query = '''SELECT fileName
                   FROM ImportedFiles
                   WHERE fileName = ?
                   '''
        with closing(conn.cursor()) as c:
            c.execute(query, (filename.name,))
            row = c.fetchone()
            
            if row:
                return True
            else:
                return False
    except sqlite3.OperationalError:
        return False

def import_sales(filename, regions):
    if not filename.isValidName:
        msg = f"File name '{filename.name}' doesn't follow the expected " + \
              f"format of '{filename.validFormat}'.\n"
        raise FileImportError(msg)
    elif filename.region == None:
        msg = f"File name '{filename.name}' doesn't include one of the " + \
              f"following region codes: {regions}.\n"
        raise FileImportError(msg)
    elif already_imported(filename):
        msg = f"File '{filename.name}' has already been imported.\n"
        raise FileImportError(msg)
    try:
        sales_list = SalesList()
        with open(filename.name, newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                daily_sales = DailySales()
                daily_sales.fromFile(row, filename.region)
                sales_list.add(daily_sales)
        return sales_list
    except FileNotFoundError:
        msg = f"File '{filename.name}' not found.\n"
        raise FileImportError(msg)
    
def add_imported_file(filename):
    sql = '''INSERT INTO ImportedFiles (fileName)
             VALUES (?)'''
    
    with closing(conn.cursor()) as c:
        c.execute(sql, (filename.name,))
        conn.commit()

def close():
    if conn:
        conn.close()





    
