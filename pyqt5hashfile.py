#!/usr/bin/env python3

import sys
import os
import hashlib
import time
import multiprocessing as mp

import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui

buffer_size = 1048576 #1Mb 

def hasher(f, stop_e, conn):
    m = hashlib.sha256()
    while True and not stop_e.is_set():
        buf = f.read(buffer_size)
        if not buf:
            break
        m.update(buf)
    f.close()
    conn.send(m.hexdigest())
    return

class hash_thread(PyQt5.QtCore.QThread):

    #cfg_update = PyQt5.QtCore.pyqtSignal()

    def __init__(self, signal, stop_e):
        super().__init__()    
        self.signal = signal
        self.signal.connect(self.got_task)
        self.stop_e = stop_e
        self.process = None
        self.conn1, self.conn2 = mp.Pipe(False)

    def run(self):
        while not self.stop_e.is_set():
            hexhash = self.conn1.recv()
            self.signal.emit({'hash':hexhash})
    
    def hash_it(self, fname):
        try:
            f = open(fname, 'rb')
        except FileNotFoundError:
            self.signal.emit({'error':'File does not exist!'})
        else:
            self.process = mp.Process(target=hasher, args=(f, self.stop_e, self.conn2))
            self.process.start()
    
    def got_task(self, data):
        if self.process is not None:
            self.process.terminate()
        if 'filepath' in data:
            if os.path.isfile(data['filepath']):
                self.hash_it(data['filepath'])
            else:
                self.signal.emit({'error':'Incorrect file!'})
        return

    def send_result(self, the_hash):
        self.signal.send({'hash':the_hash})
    

class ContextDialog(PyQt5.QtWidgets.QFileDialog):
    def __init__(self, sygnal_update):
        super().__init__()
        self.setOptions(PyQt5.QtWidgets.QFileDialog.DontUseNativeDialog)
        self.setWindowTitle('Hashes')
        self.sygnal_update = sygnal_update
        self.sygnal_update.connect(self.got_data)
        la = self.layout()
        for i in range(la.count()):
            item = la.itemAt(i)
            if type(item) == PyQt5.QtWidgets.QLayout:
                pass
            if type(item) == PyQt5.QtWidgets.QWidgetItem:
                if item.widget().objectName() == 'fileNameLabel':
                    item.widget().setText('Hash: ')
                elif item.widget().objectName() == 'fileTypeLabel':
                    item.widget().setText('Programm:')
                    item.widget().hide()
                elif item.widget().objectName() == 'fileNameEdit':
                    item.widget().hide()
                    self.hash_edit = PyQt5.QtWidgets.QLineEdit(self)
                    la.addWidget(self.hash_edit, 2, 1)
                    self.hash_edit.show()
                elif item.widget().objectName() == 'buttonBox':
                    item.widget().clear()
                    item.widget().addButton('Hash', 3)
                    #item.widget().addButton('Find', 3)
                    buttons = item.widget().buttons()
                    buttons[0].clicked.connect(self.get_hash)
                    #buttons[1].clicked.connect(self.find_hash)
                elif item.widget().objectName() == 'fileTypeCombo':
                    item.widget().hide()
                    #self.programm_edit = PyQt5.QtWidgets.QLineEdit(self)
                    #la.addWidget(self.programm_edit, 3, 1)
                    #self.programm_edit.show()
                
    def get_hash(self, event):
        self.hash_edit.clear()
        self.hash_edit.setText('Hashing...')
        self.sygnal_update.emit({'filepath':self.selectedFiles()[0]})
        
    def find_hash(self, event):
        self.programm_edit.setText('Not implemented yet')
        
    def got_data(self, data):
        if 'error' in data:
            self.hash_edit.setText(data['error'])
        elif 'hash' in data:
            self.hash_edit.setText(data['hash'])


class gui_thread(PyQt5.QtCore.QThread):
    sygnal_update = PyQt5.QtCore.pyqtSignal([dict])
    def __init__(self):
        super().__init__()
        self.dialog = ContextDialog(self.sygnal_update)
        self.dialog.show()
        
    def run(self):
        return
    

if __name__ == '__main__':
    global app
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    
    t1 = gui_thread()
    stop_e = mp.Event() #needed to stop multithreading after exit
    stop_e.clear()
    t2 = hash_thread(t1.sygnal_update, stop_e)

    t1.start()
    t2.start()
    
    app.exec_()
    stop_e.set()
    sys.exit()
