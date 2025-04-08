# ###########################################
#       Data Base SQL Class                 #
#       used mysql.comnector library        #
# ###########################################
import mysql.connector

class Database:
    def __init__(self,):
        self.connect_db()
    
    # Connect DB           
    def connect_db(self):
        try:
            self.db = mysql.connector.connect(
                 host="localhost",
                user="admin",
                password="1234",
                database="datalogger"
                
                # host="localhost",
                # user="root",
                # password="p@ssw0rd",
                # database="counterlogger"
                )    
            self.cursor = self.db.cursor()
            # print("#: Connect SQL Database complete")
        except:
            print("#: Error connecting Database")   
        
    def select_all(self):
        cmd = "SELECT * FROM logger"
        self.cursor.execute(cmd)
        for row in self.cursor.fetchall():
            print (row)
    
    def query(self,cmd):
        self.cursor.execute(cmd)
        return self.cursor.fetchall()
    
    def recordDB(self,val):
        sql = "INSERT INTO logger (timestart, count, capacity) VALUES " + str(val) 
        self.cursor.execute(sql)
        self.db.commit()
    
    def loadRecord(self):
        self.cursor.execute("SELECT COUNT(*) FROM logger")
        returnDB = self.cursor.fetchall()
        totalRecord = returnDB[0][0]
        
        # Get All customer data
        self.cursor.execute("SELECT * FROM logger ORDER BY id DESC")
        RecordDetail = self.cursor.fetchall()
        column = 5
        
        return (column,totalRecord,RecordDetail)
    
    def DeleteRecord(self,id):
        sql = "DELETE FROM logger WHERE id=" + str(id)
        self.cursor.execute(sql)
        self.db.commit()
        return self.cursor.fetchall()
    
if __name__ == "__main__":
    db = Database()
    db.connect_db()
    db.select_all()
         
