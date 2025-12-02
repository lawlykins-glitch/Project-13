#Lawkins
#12/02/2025
#Project12
import os
# Set current working directory to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

import db
import sales
from business import File, Regions, DailySales, SalesList, DATE_FORMAT, FileImportError

from decimal import Decimal, ROUND_HALF_UP

import locale as lc
lc.setlocale(lc.LC_ALL, "en_US")

def display_title():
    print("SALES DATA IMPORTER")
    print()

def display_menu():
    print("COMMAND MENU")
    print("view   - View all sales")
    print("add    - Add sales")
    print("import - Import sales from file")
    print("menu   - Show menu")
    print("exit   - Exit program")
    print()

def view_sales(sales_list):
    if sales_list.count == 0:
        print("No sales to view.\n")
    else:
        total = Decimal("0.0")
        sales_list.hasBadData = False
    
        print(f"{'':5}{'Date':15}{'Quarter':15}{'Region':10}{'Amount':>15}")
        print("-" * 60)
        for num, data in enumerate(sales_list, start=1):
            if data.hasBadData:
                sales_list.hasBadData = True
                number = f"{num}.*"  # add period and asterisk to number
            else:
                number = f"{num}."   # just add period

            amount = data.amount
            if not data.hasBadAmount:
                total += Decimal(amount)
                amount = lc.currency(amount, grouping=True)

            dt = data.salesDate
            if not data.hasBadSalesDate:
                dt = f"{dt:{DATE_FORMAT}}"

            region = data.region.name
            quarter = f"{data.quarter}"
            
            print(f"{number:5}{dt:15}{quarter:15}{region:10}{amount:>15}")

        total = total.quantize(Decimal("1.00"), ROUND_HALF_UP)
        total = lc.currency(total, grouping=True)
        print("-" * 60)
        print(f"TOTAL:{total:>54}\n")

def add_sales(sales_list, regions):
    # get the sales data
    data = DailySales()
    data.amount = sales.get_amount()
    data.salesDate = sales.get_date()
    data.region = sales.get_region(regions)
    print()

    # set quarter and add sales data to list
    data.setQuarter()
    sales_list.add(data)

    # notify user
    print(f"Sales for {data.salesDate:{DATE_FORMAT}} added.\n")

def import_sales(sales_list, regions):
    # get file name from user 
    file_name = input("Enter name of file to import: ")
    print()

    file = File(file_name)
    file.region = regions.get(file.getRegionCode())

    try:
        # import sales data from file
        imported_sales = db.import_sales(file, regions)

        # display results
        view_sales(imported_sales)

        # if has bad data, notify user to correct
        if imported_sales.hasBadData:
            print(f"File '{file.name}' contains bad data.")
            print("Please correct the data in the file and try again.\n")
        else:
            # if there are any sales, add to sales list and
            # store name of imported file
            if imported_sales.count > 0:
                sales_list.concat(imported_sales)
                print("Imported sales added to list.\n")
                db.add_imported_file(file)
                    
    except FileImportError as e:
        print(e)

def main():
    display_title()
    display_menu()

    db.connect()

    sales_list = db.get_all_sales()
    if sales_list == None:
        sales_list = SalesList()
        
    regions = db.get_regions()

    # start a loop to handle commands
    while True:
        command = input("Please enter a command: ").lower()
        if command == "view":
            view_sales(sales_list)
        elif command == "add":
            add_sales(sales_list, regions)
        elif command == "import":
            import_sales(sales_list, regions)
        elif command == "menu":
            print()
            display_menu()
        elif command == "exit":
            print()
            db.save_all_sales(sales_list)
            break
        else:
            print("Invalid command. Please try again.")
            print()
            display_menu()

    db.close()

    print("Bye!")

# if started as the main module, call the main function
if __name__ == "__main__":
    main()


    
