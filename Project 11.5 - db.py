#Lawkins
#12/02/2025
#Project12

import csv
from business import Region, Regions, DailySales, SalesList, FileImportError

import sqlite3
from contextlib import closing

conn = None

def connect():
    global conn
    if not conn:
        DB_FILE = "sales_db.sqlite"
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row

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





    
