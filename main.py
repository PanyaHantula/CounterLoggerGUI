############################################
#           Pyside 6 + Qt Designer         #
############################################
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox, QTableWidgetItem, \
                              QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot, QTimer
from PySide6.QtGui import QImage, QPixmap
import datetime
import time
import cv2
import requests

from main_gui import Ui_MainWindow
from db import *

#######################################
# IR_Count_Worker for macOS testing   #
#######################################

class IR_Count_Worker(QObject):
    IR_Count_ThreadProgress = Signal(int)
    
    def __init__(self):
        super().__init__()
    
    @Slot()
    def count(self):
        self.totalCount = 0
        while True:
            # Dummy counter
            self.totalCount += 1  
            self.IR_Count_ThreadProgress.emit(self.totalCount)   
            time.sleep(2)

    def reset(self):
        self.totalCount = 0

# ###################################
# #  IR_Count_Worker  for rasp pi   #
# ###################################
# import RPi.GPIO as GPIO

# # Pin of Input
# GPIOpin_IR1 = -1
# GPIOpin_IR2 = -1

# class IR_Count_Worker(QObject):
#     IR_Count_ThreadProgress = Signal(int)
    
#     def __init__(self):
#         super().__init__()
#         IR_1 = 23
#         IR_2 = 24
#         self.initialInductive(IR_1,IR_2)
#         # self.initialInductive(IR_2)

#     # Initial the input pin
#     def initialInductive(self,IR1,IR2):
#         global GPIOpin_IR1 
#         global GPIOpin_IR2
        
#         GPIOpin_IR1 = IR1
#         GPIOpin_IR2 = IR2
        
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(GPIOpin_IR1,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#         GPIO.setup(GPIOpin_IR2,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#         # print(f"Finished Initiation : Port {GPIOpin_IR1} and Port {GPIOpin_IR2}")
    
#     @Slot()
#     def count(self):
#         self.totalCount = 0
#         while True:
#             # # Dummy counter
#             # self.totalCount += 1  
#             # self.IR_Count_ThreadProgress.emit(self.totalCount)   
#             # time.sleep(2)
            
#             # Test GPIO Port
#             state1 = GPIO.input(GPIOpin_IR1)
#             state2 = GPIO.input(GPIOpin_IR2)
#             #print(f"GPIO State1: {state1} ,State2: {state2} ")
            
#             if state1 == 0 or state2 == 0:
#                 while state1 == 0 or state2 == 0:
#                     state1 = GPIO.input(GPIOpin_IR1)
#                     state2 = GPIO.input(GPIOpin_IR2)
                    
#                 # print("Metal Detected")
#                 self.totalCount += 1   
#                 # print(f"Detected -> Counter : {self.totalCount}")
#                 self.IR_Count_ThreadProgress.emit(self.totalCount)       
#             time.sleep(0.1)
    
#     def reset(self):
#         self.totalCount = 0

###################################
#          CameraWorker           #
###################################
class CameraWorker(QObject):
    frameCaptured = Signal(object)  # Emit frame data

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.camera_index = 0
        self.running = False

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.camera_index)
        # ตั้งค่าการบันทึกวิดีโอ
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 20  # เฟรมต่อวินาที
        record_seconds =  10              # 5 * 60  # 5 นาที = 300 วินาที
        num_files = 10

        # โฟลเดอร์เก็บไฟล์
        output_folder = "videos"
        os.makedirs(output_folder, exist_ok=True)

        file_index = 0  # เริ่มที่ไฟล์แรก

        try:
            while self.running:
                filename = os.path.join(output_folder, f"video_{file_index}.mp4")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # ใช้ codec mp4
                out = cv2.VideoWriter(filename, fourcc, fps, (frame_width, frame_height))

                print(f"กำลังบันทึก: {filename}")
                start_time = time.time()
                
                while time.time() - start_time < record_seconds:
                    ret, frame = cap.read()
                    if not ret:
                        print("ไม่สามารถอ่านภาพจากกล้องได้")
                        break
                    
                    # วาดเวลาปัจจุบัน
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, current_time, (10, frame_height - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    # แสดง capacity
                    Capacity = self.main_window.ui.lbl_capacity.text()
                    cv2.putText(frame, f"Capacity: {Capacity}", (10, frame_height - 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    # แสดง Counter
                    CountTotal = self.main_window.ui.lbl_counter.text()
                    cv2.putText(frame, f"Total: {CountTotal}", (10, frame_height - 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)               
                    
                    out.write(frame)
                    #cv2.imshow('Recording...', frame)
                    self.frameCaptured.emit(frame)
                
                out.release()
                
                # เปลี่ยนไฟล์ถัดไป (วนกลับไปที่ไฟล์แรกเมื่อครบ 10 ไฟล์)
                file_index = (file_index + 1) % num_files
                
        except KeyboardInterrupt:
            print("หยุดการบันทึก")

        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def add_overlay(self, frame):
        # เพิ่มเวลาปัจจุบัน
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, current_time, (10, self.frame_height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return frame
                        
    def stop(self):
        self.running = False

    
###################################
#           MainWindow            #
###################################                
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # self.showMaximized()
        self.setWindowTitle("Counter Logger")
        
        # connect to DB
        self.db = Database()
        self.db.connect_db()
        self.loadDatabase()
        
        self.setClock()         # set Clock       
        self.setThread()        # Initialize worker and thread
        self.resetData()        # Stop Thread befor reset   
        
        # set button
        self.ui.btn_save.clicked.connect(self.recordDB)
        self.ui.btn_delete.clicked.connect(self.deleteRecord)
        self.ui.btn_exit.clicked.connect(self.exit)

        self.scene = QGraphicsScene()
        self.ui.gp_camera.setScene(self.scene)
        self.scenePixmapItem = None
        
    # Initialize worker and thread
    def setThread(self):
        # IR Counter
        self.IR_Count_thread = QThread()
        self.IR_Count_thread.setObjectName('IR_Count_thread')   # Create thread 
        self.IR_Count_Worker = IR_Count_Worker()                # Create worker
        self.IR_Count_Worker.moveToThread(self.IR_Count_thread) # move worker to thread 
        self.IR_Count_thread.started.connect(self.IR_Count_Worker.count)     # Connect Thread
        self.IR_Count_Worker.IR_Count_ThreadProgress.connect(self.UpdateTotalCount)     # Connect signals and slots
        self.IR_Count_thread.start()    # Start Thread
        
        # camera thread
        self.thread = QThread()
        self.cameraWorker = CameraWorker(self)
        self.cameraWorker.moveToThread(self.thread)
        self.cameraWorker.frameCaptured.connect(self.processFrame)
        self.thread.started.connect(self.cameraWorker.run)
        self.thread.start()
    
    ####### Process frame camera
    def processFrame(self, frame):
        # Convert the frame to a format that Qt can use
        image = QImage(
            frame.data,
            frame.shape[1],
            frame.shape[0],
            QImage.Format.Format_BGR888,
        )
        pixmap = QPixmap.fromImage(image)

        if self.scenePixmapItem is None:
            self.scenePixmapItem = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.scenePixmapItem)
            self.scenePixmapItem.setZValue(0)
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.scenePixmapItem.setPixmap(pixmap)

    def stopCamera(self):
        self.cameraWorker.stop()
        self.thread.quit()
        self.thread.wait()

    def fitInView(self, rect, aspectRatioMode):
         self.ui.gp_camera.fitInView(rect, aspectRatioMode)
      
    # Count and cal Preformance      
    def UpdateTotalCount(self,count):
        self.ui.lbl_counter.setText(str(count))
        
        # Cal Preformance
        totalTimeMinute = float((datetime.datetime.now() - self.startTime ).total_seconds()/60)
        if totalTimeMinute > 0:
            Performance = int(self.ui.lbl_counter.text()) / totalTimeMinute
        else:
            Performance = 0
        self.ui.lbl_capacity.setText("{:.2f}".format(Performance)) 
           
    # Record data to data base 
    def recordDB(self):
        startTime = self.ui.lbl_StartTime.text()
        CountTotal = self.ui.lbl_counter.text()
        capacity = self.ui.lbl_capacity.text()
        
        dlg = QMessageBox(self)
        dlg.setWindowTitle("บันทึกข้อมูล")
        dlg.setText("ต้องการบันข้อมูลผู้ใช้งานหรือไม่ ??\n หมายเหตุ: หลังจากกดบันทึกแล้ว ข้อมูลที่หน้าจอจะหายไป")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        button = dlg.exec()
        
        if button == QMessageBox.Yes:
            val = (startTime,CountTotal,capacity)
            self.db.recordDB(val)
            self.loadDatabase()
            self.resetData()
            
            # Upload to google sheet
            url = 'https://script.google.com/macros/s/AKfycbxGkiEN9ZShcJoMqW-IOJKxcDx41E_6MyvSluE8TibDH1_SURXXRmKINAAKk_OyfHES/exec?'\
                  'timestart=' + startTime + '&total=' + CountTotal + '&capacity=' + capacity
            response = requests.get(url)
            print(response)
                
    # Load data form DB and update to table view        
    def loadDatabase(self):
        column,totalRecord,RecordDetail = self.db.loadRecord()

        # create Table
        self.ui.tb_logger.setRowCount(totalRecord)
        self.ui.tb_logger.setColumnCount(column)
        self.ui.tb_logger.setHorizontalHeaderItem(0, QTableWidgetItem("NO"))
        self.ui.tb_logger.setHorizontalHeaderItem(1, QTableWidgetItem("เวลาบันทึก"))
        self.ui.tb_logger.setHorizontalHeaderItem(2, QTableWidgetItem("เวลาเริ่มงาน"))
        self.ui.tb_logger.setHorizontalHeaderItem(3, QTableWidgetItem("จำนวนที่ผลิตได้(ชิ้น)"))
        self.ui.tb_logger.setHorizontalHeaderItem(4, QTableWidgetItem("กำลังการผลิต(ชิ้น/นาที)"))
        
        header = self.ui.tb_logger.horizontalHeader()         
        for col in range(column):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            
        tablerow = 0
        for row in RecordDetail:
            self.ui.tb_logger.setItem(tablerow,0,QTableWidgetItem(str(row[0])))
            self.ui.tb_logger.setItem(tablerow,1,QTableWidgetItem(str(row[1])))
            self.ui.tb_logger.setItem(tablerow,2,QTableWidgetItem(str(row[2])))
            self.ui.tb_logger.setItem(tablerow,3,QTableWidgetItem(str(row[3])))
            self.ui.tb_logger.setItem(tablerow,4,QTableWidgetItem(str(row[4])))
            tablerow += 1
    
    # delete data in DB
    def deleteRecord(self):
        id = self.ui.tb_logger.item(self.ui.tb_logger.currentIndex().row(),0).text()
        timeStampToDelete = self.ui.tb_logger.item(self.ui.tb_logger.currentIndex().row(),1).text()
        SelectRowToDetete = self.ui.tb_logger.currentRow()
        
        dlg = QMessageBox(self)
        dlg.setWindowTitle("ลบข้อมูล")
        dlg.setText("ต้องการลบข้อมูลผู้ใช้งานหรือไม่ ??\n " + timeStampToDelete)
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        button = dlg.exec()
        
        if button == QMessageBox.Yes:
            if SelectRowToDetete < 0:
                return
            self.ui.tb_logger.removeRow(SelectRowToDetete)
            self.db.DeleteRecord(id)
            
            # Refresh Table User
            self.loadDatabase()
        
        # reset value in thread 
    
    def resetData(self):
        self.ui.lbl_counter.setText("0")
        self.ui.lbl_capacity.setText("0")  
        self.startTime = datetime.datetime.now()
        self.ui.lbl_StartTime.setText(str(self.startTime.strftime("%H:%M:%S")))
        self.IR_Count_Worker.reset()
      
    # method called by timer    
    def setClock(self):
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000)
       
    def showTime(self):
        label_time = datetime.datetime.now().strftime("%H:%M")
        self.ui.lbl_time.setText(label_time)
        
        dateNow = datetime.datetime.now().strftime("%Y-%m-%d")
        self.ui.lbl_date.setText(dateNow)
    
    def exit(self):
        self.close()
                   
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()   
    window.stopCamera()
