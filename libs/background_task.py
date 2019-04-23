from PyQt5.QtCore import *

all_stop = False
 
class TaskSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)
    
class BackgroundTask(QRunnable):
#class BackgroundTask(QThread):
    quit_thread = pyqtSignal(name='close_thread')

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.func = func
        self.lock = None
        self.signals = TaskSignals()
        self.loop = 1
        
    def setLock(self, lock):
        self.lock = lock
        
    def setLoop(self, loop):
        self.loop = loop
            
    @pyqtSlot()                
    def run(self):
        global all_stop
        while all_stop == False and self.loop != 0:
            if self.lock is not None:
                print("lock")
                self.lock.lock()
                results = self.func(*self.args, **self.kwargs)
                self.lock.unlock()
                print("unlock")
            else:
                print("Run async call without lock")
                results = self.func(*self.args, **self.kwargs)
            self.signals.result.emit(results)
            self.signals.finished.emit()
            self.loop -= 1
            
"""https://stackoverflow.com/questions/46511239/pyqt-qthreadpool-with-qrunnables-taking-time-to-quit/46514607#46514607"""            
class ThreadManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = self.get_tasks()
        self.timer = QTimer()
        self.threads = []
        
    def start(self):
        self.create_tasks()
        self.timer.setInterval(3000)
        self.timer.start()
        self.timer.timeout.connect(self.create_tasks)
        
    @staticmethod
    def get_tasks():
        pass
           

def run_async(callback, func, *args, **kwargs):
    task = BackgroundTask(func, *args, **kwargs)
    if callback:
        task.signals.result.connect(callback)
    QThreadPool.globalInstance().start(task);

def run_async_mutex(lock, callback, func, *args, **kwargs):
    task = BackgroundTask(func, *args, **kwargs)
    task.setLock(lock)
    if callback:
        task.signals.result.connect(callback)
    QThreadPool.globalInstance().start(task);
    
def run_loop(loop, callback, func, *args, **kwargs):
    task = BackgroundTask(func, *args, **kwargs)
    task.setLoop(loop)
    if callback:
        task.signals.result.connect(callback)
    QThreadPool.globalInstance().start(task);
    
def run_loop_mutex(loop, lock, callback, func, *args, **kwargs):
    task = BackgroundTask(func, *args, **kwargs)
    task.setLock(lock)
    task.setLoop(loop)
    if callback:
        task.signals.result.connect(callback)
    QThreadPool.globalInstance().start(task)

def remove_threads():
    global all_stop
    all_stop = True
    #QThreadPool.globalInstance().clear()
