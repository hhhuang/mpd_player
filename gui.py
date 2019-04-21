import datetime
import json
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *
 
from mpd_client import * 


def createTrackTable():
    """'time': '291', 'artist': 'Yvonne Lefebure', 'title': 'Le Tombeau de Couperin - Forlane', 'track': '3', 'disc': '0', """
    # Create table
    table = QTableWidget()
    table.setRowCount(0)
    table.setColumnCount(5)
    table.setHorizontalHeaderLabels(["Disc", "Track", "Title", "Artist", "Length"])
    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(2, QHeaderView.Stretch)
    header.setSectionResizeMode(3, QHeaderView.Stretch)
    header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
    return table

    
def updateTrackTable(table, tracks, key_field):
    table.setRowCount(len(tracks))
    for i in range(len(tracks)):
        track = tracks[i]
        title = QTableWidgetItem(track['title'])
        title.setData(Qt.UserRole, track[key_field])
        table.setItem(i, 0, QTableWidgetItem(str(track['disc'])))
        table.setItem(i, 1, QTableWidgetItem(str(track['track'])))
        table.setItem(i, 2, title)
        table.setItem(i, 3, QTableWidgetItem(track['artist']))
        table.setItem(i, 4, QTableWidgetItem(str(datetime.timedelta(seconds=int(track['time'])))))
        table.move(0,0)
    for i in range(table.rowCount()):
        for j in range(table.columnCount()):
            table.item(i, j).setFlags(table.item(i, j).flags() ^ Qt.ItemIsEditable)
    
    
class AlbumPopup(QDialog):
    def __init__(self, main, album):
        super().__init__(main)
        self.name = "Album"
        self.main = main
        self.album = album

        self.setWindowTitle(album.title + " - " + album.artist)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowSystemMenuHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.createAlbumSection())        
        self.layout.addWidget(self.createTrackSection())        
        self.layout.addWidget(self.createControlSection())        
        self.setLayout(self.layout) 
        self.show()
        
    def createAlbumSection(self):
        grid = QGridLayout()
        grid.addWidget(QLabel("Title: ", self), 0, 0)
        grid.addWidget(QLabel(self.album.title, self), 0, 1)
        grid.addWidget(QLabel("Artist: ", self), 1, 0)
        grid.addWidget(QLabel(self.album.artist, self), 1, 1)
        grid.addWidget(QLabel("Last modified: ", self), 2, 0)
        grid.addWidget(QLabel(self.album.last_modified, self), 2, 1)
    
        section = QGroupBox()
        section.setLayout(grid)
        return section
        
    def createTrackSection(self):
        self.table = createTrackTable()
        updateTrackTable(self.table, self.album.tracks, 'file')
        #        self.albumTable.doubleClicked.connect(self.item_on_double_click)
        self.table.clicked.connect(self.item_on_click)           
        return self.table
               
        
    def createControlSection(self):
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.setFixedSize(QSize(50, 20))
        self.cancel_button.clicked.connect(self.cancel_on_click)
                
        self.play_button = QPushButton('Play', self)
        self.play_button.setFixedSize(QSize(50, 20))
        self.play_button.clicked.connect(self.play_on_click)

        section = QGroupBox()
        section.setLayout(QHBoxLayout())
        section.layout().addWidget(self.cancel_button)
        section.layout().addWidget(self.play_button)
        return section

    @pyqtSlot()
    def item_on_click(self):
        for currentQTableWidgetItem in self.table.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())
            self.table.setRangeSelected(QTableWidgetSelectionRange(currentQTableWidgetItem.row(), 0, currentQTableWidgetItem.row(), self.table.columnCount() - 1), True)
    
    @pyqtSlot()
    def cancel_on_click(self):
        self.close()
        
    @pyqtSlot()
    def play_on_click(self):
        print(self.album.title)         
        self.main.player.pause()
        self.main.playqueue.clear()        
        if not self.table.selectedItems():
            self.main.playqueue.add_album(self.album, self.main.player.play)
            return
        files = [item.data(Qt.UserRole) for item in self.table.selectedItems() if item.column() == 2]
        print(files)
        self.main.playqueue.add_files(files, self.main.player.play)
        self.main.updatePlaylist()
        self.close()
        
        
class ConfigPopup(QDialog):
    def __init__(self, main):
        super().__init__(main)
        self.name = "Configuration"
        self.main = main

        self.setWindowTitle("Configuration")
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowSystemMenuHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        
        self.host_label = QLabel("Host: ", self)
        self.host_input = QLineEdit(main.config['host'], self)
        self.host_input.setFixedSize(QSize(200, 20))
        
        self.port_label = QLabel("Port: ", self)
        self.port_input = QLineEdit(str(main.config['port']), self)
        self.port_input.setFixedSize(QSize(200, 20))
        
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.setFixedSize(QSize(50, 20))
        self.cancel_button.clicked.connect(self.cancel_on_click)
                
        self.ok_button = QPushButton('Ok', self)
        self.ok_button.setFixedSize(QSize(50, 20))
        self.ok_button.clicked.connect(self.ok_on_click)
        
        self.layout = QGridLayout()
        self.layout.addWidget(self.host_label, 0, 0)
        self.layout.addWidget(self.host_input, 0, 1)
        self.layout.addWidget(self.port_label, 1, 0)
        self.layout.addWidget(self.port_input, 1, 1)
        self.layout.addWidget(self.cancel_button, 2, 0)
        self.layout.addWidget(self.ok_button, 2, 1)
        
        self.setLayout(self.layout) 
        self.show()
        
    @pyqtSlot()
    def cancel_on_click(self):
        self.close()
        
    @pyqtSlot()
    def ok_on_click(self):
        self.main.config['host'] = self.host_input.text().strip()
        self.main.config['port'] = int(self.port_input.text().strip())
        self.main.save_config()
        self.main.initMPD()
        self.close()
"""
class AsyncRunnable(object):
    class BackgroundTask(QRunnable):
        def __init__(self, func, *args):
            super(BackgroundTask, self).__init__()
            self.args = args
            self.func = func
            self.lock = None
                       
        def setLock(self, lock):
            self.lock = lock
                
        def run(self):
            if self.lock:
                if self.lock.tryLock():
                    print("Run async call with lock")
                    self.func(*self.args)
                    self.lock.unlock()
                else:
                    print("Fail to lock")
            else:
                print("Run async call without lock")
                self.func(*self.args)

    def run_async(func, *args):
        task = BackgroundTask(func, *args)
        QThreadPool.globalInstance().start(task);
            
    def run_async_mutex(lock, func, *args):
        task = BackgroundTask(func, *args)
        task.setLock(lock)
        task.run()
        #QThreadPool.globalInstance().start(task);

        
class AsyncPlayQueue(PlayQueue, AsyncRunnable):
    def __init__(self, *args):
        super(AsyncPlayQueue, self).__init__(*args)
        self.lock = QMutex()
        
    def async_add_albums(self, albums):
        self.run_async_mutex(self.lock, add_albums, albums)
"""

class App(QMainWindow): 
    def __init__(self):
        super().__init__()
        self.load_config()
        self.title = 'MPD Controller'
        self.left = 0
        self.top = 0
        self.width = 1024
        self.height = 768
        self.initUI()
        self.initMPD()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000);
        
    def __del__(self):
        self.mpd_server.close()
        self.mpd_server.disconnect()    
        
    def load_config(self):
        try:
            with open("config.json") as fin:
                self.config = json.load(fin)            
        except:
            self.config = {'host': '192.168.11.235', 'port': 6601}
            
    def save_config(self):
        with open("config.json", "w") as fout:
            json.dump(self.config, fout)
        
    def initMPD(self):
        self.mpd_server = connect_server(self.config['host'], self.config['port'])
        self.music_lib = Library(self.mpd_server, update=False)
        self.playqueue = PlayQueue(self.mpd_server)
        self.player = Player(self.mpd_server)
        self.updateAlbumTable(self.music_lib.list_latest_albums(10000000))  
        self.updatePlaylist()
        
    def createMenuBar(self):
        self.config_action = QAction("Configuration", self)
        self.config_action.triggered.connect(self.popup_configuration)

        self.rebuild_action = QAction("Rebuild Library", self)
        self.rebuild_action.triggered.connect(self.rebuild_library)
        
        self.menuBar = QMenuBar()
        self.config_menu = self.menuBar.addMenu('Options')
        self.config_menu.addAction(self.config_action)
        self.config_menu.addAction(self.rebuild_action)
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.statusBar = QStatusBar(self)
        self.createMenuBar()
        self.createControlPanel()  
        self.createAlbumTable()
        self.playlist = createTrackTable()
        self.playlist.clicked.connect(self.playlist_on_click)            
        self.renderLayout()
                
    def renderLayout(self):
        self.layout = QVBoxLayout()
        self.layout.setMenuBar(self.menuBar)
        self.layout.addWidget(self.controlPanel)
        
        #self.album_tab = QFrame()
        #self.album_tab.setLayout(QVBoxLayout())
        #self.album_tab.layout().addWidget(self.albumTable)
        #self.album_tab.layout().addWidget(self.statusBar)
        
        #self.playlist_tab = QFrame()
        #self.playlist_tab.setLayout(QVBoxLayout())
        #self.playlist_tab.layout().addWidget(self.playlist)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.albumTable, "Albums")
        self.tabs.addTab(self.playlist, "Playlist")
        
        self.layout.addWidget(self.tabs) 
        self.layout.addWidget(self.statusBar)
        self.setLayout(self.layout) 
        self.show()
                    
    def updateStatusBar(self, albums):
        num_discs = 0
        num_tracks = 0
        total_seconds = 0
        for album in albums:
            album_discs = set()
            for track in album.tracks:
                album_discs.add(track['disc'])
                total_seconds += int(track['time'])
            num_tracks += len(album.tracks)
            num_discs += len(album_discs)
        status = "Number of albums: %d, Number of disks: %d, Number of tracks: %d, Total time: %s" % (len(albums), num_discs, num_tracks, str(datetime.timedelta(seconds=total_seconds)))
        self.statusBar.showMessage(status)
        
    def createControlPanel(self):
        self.play_button = QPushButton('Play', self)
        self.play_button.setFixedSize(QSize(50, 20))
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.play_on_click)
               
        self.infobox = QLineEdit("", self)
        self.infobox.setReadOnly(True)
        
        self.time_info = QLabel("", self)
        self.time_info.setFixedSize(QSize(40, 20))
        
        self.seek_slider = QSlider(Qt.Horizontal, self)
        self.seek_slider.setFixedSize(QSize(120, 20))
        self.seek_slider.sliderMoved.connect(self.slider_moved)
        
        self.search_box = QLineEdit("", self)
        self.search_box.setFixedSize(QSize(120, 20))
        self.search_box.returnPressed.connect(self.search_box_entered)
        self.search_button = QPushButton('Search', self)
        self.search_button.setFixedSize(QSize(50, 20))
        self.search_button.clicked.connect(self.search_on_click)
                
        layout = QHBoxLayout()
        layout.addWidget(self.play_button)
        layout.addWidget(self.infobox)
        layout.addWidget(self.seek_slider)
        layout.addWidget(self.time_info)
        layout.addWidget(self.search_box)
        layout.addWidget(self.search_button)
        
        self.controlPanel = QGroupBox()               
        self.controlPanel.setLayout(layout)

    @pyqtSlot()
    def playlist_on_click(self):
        songid = [item.data(Qt.UserRole) for item in self.playlist.selectedItems() if item.column() == 2][0]
        print(songid)
        self.player.playid(songid)
            
    @pyqtSlot()
    def update_status(self):
        track = self.playqueue.get_current_song()        
        status = self.player.status()
        if track and status and 'time' in status:
            self.infobox.setText("%s: %d-%d %s %s" % (track['album'], int(track['disc']), int(track['track']), track['title'], track['artist']))
            playing_time = status['time'].split(":")[:-1][0]
            self.time_info.setText("%s/%s" % (playing_time, track['time']))
            self.seek_slider.setMinimum(0)            
            self.seek_slider.setMaximum(int(track['time']))
            self.seek_slider.setValue(int(playing_time))
            if status['state'] == 'play':
                self.play_button.setChecked(True)
                self.play_button.setText('Pause')
            else:
                self.play_button.setChecked(False)
                self.play_button.setText('Play')
            #   Highlight the playing track in the playlist.
            self.playlist.setRangeSelected(QTableWidgetSelectionRange(0, 0, self.playlist.rowCount() - 1, self.playlist.columnCount() - 1), False)
            self.playlist.setRangeSelected(QTableWidgetSelectionRange(int(track['pos']), 0, int(track['pos']), self.playlist.columnCount() - 1), True)
        else:
            self.infobox.setText("")
            self.time_info.setText("")
            self.play_button.setChecked(False)
            self.play_button.setText('Play')
            self.seek_slider.setValue(0)
            
    @pyqtSlot()
    def slider_moved(self):
        self.player.seek(self.seek_slider.value())
            
    @pyqtSlot()
    def play_on_click(self):
        if self.play_button.text() == 'Pause':
            self.play_button.setChecked(False)
            self.play_button.setText('Play')
            self.player.pause()
        else:
            self.play_button.setChecked(True)
            self.play_button.setText('Pause')
            self.play_selected()

    @pyqtSlot()
    def stop_on_click(self):
        self.player.pause()

    @pyqtSlot()
    def search_box_entered(self):
        self.search()
        
    @pyqtSlot()
    def search_on_click(self):
        self.search()
       
    @pyqtSlot()
    def popup_configuration(self):
        exPopup = ConfigPopup(self)
        exPopup.setGeometry(100, 200, 100, 100)
        exPopup.show()

    @pyqtSlot()
    def rebuild_library(self):
        self.music_lib = Library(self.mpd_server, update=True)
        self.updateAlbumTable(self.music_lib.list_latest_albums(10000000))  
    
    def search(self):
        query = self.search_box.text().strip()
        print(query)
        if not query:
            albums = self.music_lib.list_latest_albums(10000000)
        else:
            albums = self.music_lib.search(query.split())
        print("Number of albums found: %d" % len(albums))
        self.updateAlbumTable(albums)

    def updateAlbumTable(self, albums):
        self.fillAlbumTable(albums)
        self.layout.update()
        self.update()
        
    def fillAlbumTable(self, albums):
        self.albumTable.clearContents()
        self.albumTable.setRowCount(len(albums))
        
        for i in range(len(albums)):
            title = QTableWidgetItem(albums[i].title)
            title.setData(Qt.UserRole, albums[i].album_id)
            self.albumTable.setItem(i, 0, title)
            self.albumTable.setItem(i, 1, QTableWidgetItem(albums[i].artist))
            self.albumTable.setItem(i, 2, QTableWidgetItem(albums[i].last_modified[:10]))
        self.albumTable.move(0,0)
        for i in range(self.albumTable.rowCount()):
            for j in range(self.albumTable.columnCount()):
                self.albumTable.item(i, j).setFlags(self.albumTable.item(i, j).flags() ^ Qt.ItemIsEditable)
        self.sorted_order = Qt.DescendingOrder
        self.sorted_column = 2
        self.albumTable.sortItems(self.sorted_column, self.sorted_order)
        self.updateStatusBar(albums)
        
    def updatePlaylist(self):
        """'file': 'file:/disk2/share/Music/Music/Leif Ove Andsnes/Sibelius/05 Sibelius_ Kyllikki, Op. 41 - 3. C.m4a', 
        'last-modified': '2018-12-21T13:57:59Z', 
        'time': '175', 'artist': 'Leif Ove Andsnes', 'albumartist': 'Leif Ove Andsnes', 'artistsort': 'Leif Ove Andsnes', 'albumartistsort': 'Leif Ove Andsnes', 'album': 'Sibelius', 'title': 'Sibelius: Kyllikki, Op. 41 - 3. Commodo', 'track': '5', 'date': '2017', 'genre': 'Classical', 'disc': '1', 'pos': '4', 'id': '46227'}"""
        updateTrackTable(self.playlist, self.playqueue.list(), 'id')
#        self.albumTable.doubleClicked.connect(self.item_on_double_click)
#        self.playlist.clicked.connect(self.item_on_click)           
       
        
    def createAlbumTable(self):
        # Create table
        self.albumTable = QTableWidget()
        self.albumTable.setRowCount(0)
        self.albumTable.setColumnCount(3)
        self.albumTable.setHorizontalHeaderLabels(["Title", "Aritst", "Last Modified"])
        header = self.albumTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.sectionClicked.connect(self.header_on_click)      
        
        row = self.albumTable.verticalHeader()
        row.sectionClicked.connect(self.row_on_click)
        
        # table selection change
        self.albumTable.doubleClicked.connect(self.item_on_double_click)
        self.albumTable.clicked.connect(self.item_on_click)
    
    @pyqtSlot()
    def item_on_click(self):
        for currentQTableWidgetItem in self.albumTable.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())
            self.albumTable.setRangeSelected(QTableWidgetSelectionRange(currentQTableWidgetItem.row(), 0, currentQTableWidgetItem.row(), self.albumTable.columnCount() - 1), True)

    @pyqtSlot()
    def item_on_double_click(self):
        for currentQTableWidgetItem in self.albumTable.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())
            self.albumTable.setRangeSelected(QTableWidgetSelectionRange(currentQTableWidgetItem.row(), 0, currentQTableWidgetItem.row(), self.albumTable.columnCount() - 1), True)
        self.popup_album()
    
    def popup_album(self):
        album_ids = set([item.data(Qt.UserRole) for item in self.albumTable.selectedItems() if item.column() == 0])
        album = self.music_lib.get_album(list(album_ids)[0])
        exPopup = AlbumPopup(self, album)
        exPopup.setGeometry(100, 100, 800, 600)
        exPopup.show()
        
    @pyqtSlot()
    def row_on_click(self):
        self.play_selected()
        
    @pyqtSlot()
    def header_on_click(self):
        column = self.albumTable.selectedItems()[0].column()
        if column == self.sorted_column:
            if self.sorted_order == Qt.AscendingOrder:
                self.sorted_order = Qt.DescendingOrder
            else:
                self.sorted_order = Qt.AscendingOrder
        else:
            if column == 2:
                self.sorted_order = Qt.DescendingOrder
            else:
                self.sorted_order = Qt.AscendingOrder
            
        self.albumTable.sortItems(column, self.sorted_order)
        self.sorted_column = column
            
    def play_selected(self):
        if not self.albumTable.selectedItems():
            self.player.play()
            return
        album_ids = set([item.data(Qt.UserRole) for item in self.albumTable.selectedItems() if item.column() == 0])
        print(album_ids)
        self.player.pause()
        self.playqueue.clear()
        albums = []
        for album_id in album_ids:
            albums.append(self.music_lib.get_album(album_id))
            
        print("Adding album")
        self.playqueue.async_add_albums(albums) #, self.player.play)
        print("Job sent")
        self.updatePlaylist()
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
    