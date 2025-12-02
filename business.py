#Lawkins
#12/02/2025
#Project12

from datetime import datetime, date
from dataclasses import dataclass

# constant for working with dates
DATE_FORMAT = "%Y-%m-%d"

class FileImportError(OSError):
    pass

@dataclass
class Region:
    code:str = ""
    name:str = ""

class Regions:
    def __init__(self):
        self.__VALID_REGIONS = []

    def __str__(self):
        regions = []
        for region in self.__VALID_REGIONS:
            regions.append(region.code)
        return str(regions)

    def get(self, code):
        for region in self.__VALID_REGIONS:
            if code == region.code:
                return region
        return None

    def add(self, region):
        self.__VALID_REGIONS.append(region)

@dataclass
class File:
    name:str = ""
    region:Region = None
    __NAMING_CONVENTION = "sales_qn_yyyy_r.csv"

    @property
    def isValidName(self):
        if len(self.name) == len(self.__NAMING_CONVENTION) and \
           self.name[:7] == self.__NAMING_CONVENTION[:7] and \
           self.name[8] == self.__NAMING_CONVENTION[8] and \
           self.name[13] == self.__NAMING_CONVENTION[13] and \
           self.name[-4:] == self.__NAMING_CONVENTION[-4:]:
            return True
        else:
            return False

    @property
    def validFormat(self):
        return self.__NAMING_CONVENTION

    def getRegionCode(self):
        # region code is 5th from last character in file name
        return self.name[-5]          

@dataclass
class DailySales:
    amount:float = 0.0
    salesDate:date = None
    region:Region = None
    quarter:int = 0
    id:int = 0

    @property
    def hasBadAmount(self):
        if self.amount == "?":
            return True
        else:
            return False
    
    @property
    def hasBadSalesDate(self):
        if self.salesDate == "?":
            return True
        else:
            return False
    
    @property
    def hasBadData(self):
        if self.hasBadAmount or self.hasBadSalesDate:
            return True
        else:
            return False

    def fromFile(self, row, region):
        # amount
        try:
            self.amount = float(row[0])
        except ValueError:
             self.amount = "?"

        # date
        try:
            dt = datetime.strptime(row[1], DATE_FORMAT)
            # convert to a date object rather than a datetime object
            self.salesDate = date(dt.year, dt.month, dt.day)
        except ValueError:
            self.salesDate = "?"

        # region
        self.region = region

        # quarter
        self.setQuarter()
        
    def fromDb(self, row):
        self.amount = row["amount"]
        self.region = Region(row["code"], row["name"])
        self.id = row["ID"]

        # no validation bc only good data is stored in db
        self.salesDate = datetime.strptime(row["salesDate"], DATE_FORMAT)
        
        self.setQuarter()
        
    def toList(self):
        if self.hasBadData:
            return None
        else:
            return [self.amount, self.salesDate, self.region.code]
        
    def setQuarter(self):
        if self.hasBadSalesDate == True:
            self.quarter = 0
        else:
            if self.salesDate.month >=1 and self.salesDate.month <= 3:
                self.quarter = 1
            elif self.salesDate.month >= 4 and self.salesDate.month <=6:
                self.quarter = 2
            elif self.salesDate.month >= 7 and self.salesDate.month <=9:
                self.quarter = 3
            elif self.salesDate.month >= 10 and self.salesDate.month <=12:
                self.quarter = 4       

class SalesList:
    def __init__(self):
        self.__sales = []
        self.hasBadData = False

    @property
    def count(self):
        return len(self.__sales)

    def get(self, index):
        if index >= self.count:
            return None
        else:
            return self.__sales[index]

    def add(self, data):
        self.__sales.append(data)

    def concat(self, sales_list):
        for i in range(sales_list.count):
            self.add(sales_list.get(i))

    def __iter__(self):
        for data in self.__sales:
            yield data

def main():
    pass

# if started as the main module, call the main function
if __name__ == "__main__":
    main()


    
