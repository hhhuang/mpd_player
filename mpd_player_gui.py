import datetime
import json
import os
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtCore import *
 
from mpd_client import * 
from libs.background_task import run_async, run_async_mutex, run_loop, remove_threads

from kb.kb_prediction import get_recommendation_list

def createRecommendationGrid():
   # Create table
    table = QTableWidget()
    table.setShowGrid(False)
    table.horizontalHeader().hide()
    table.verticalHeader().hide()
    #table.setRowCount((len(items) + 2) // 3)
    table.setColumnCount(8)
    table.setColumnWidth(0, 150)
    table.setColumnWidth(1, 150)
    table.setColumnWidth(2, 15)
    table.setColumnWidth(3, 150)
    table.setColumnWidth(4, 150)
    table.setColumnWidth(5, 15)
    table.setColumnWidth(6, 150)
    table.setColumnWidth(7, 150)
    return table

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
        title = TableItem(track['title'])
        title.setData(Qt.UserRole, track[key_field])
        table.setItem(i, 0, TableItem(str(track['disc'])))
        table.setItem(i, 1, TableItem(str(track['track'])))
        table.setItem(i, 2, title)
        table.setItem(i, 3, TableItem(track['artist']))
        table.setItem(i, 4, TableItem(str(datetime.timedelta(seconds=int(track['time'])))))
        table.move(0,0)
        
    
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
        self.cancel_button.clicked.connect(self.cancel_on_click)
                
        self.play_button = QPushButton('Play', self)
        self.play_button.clicked.connect(self.play_on_click)

        section = QGroupBox()
        section.setLayout(QHBoxLayout())
        section.layout().addWidget(self.cancel_button)
        section.layout().addWidget(self.play_button)
        return section

    @pyqtSlot()
    def item_mouse_over(self):
        """        ▶"""
        pass
        
    @pyqtSlot()
    def item_on_click(self):
        for currentTableItem in self.table.selectedItems():
            print(currentTableItem.row(), currentTableItem.column(), currentTableItem.text())
            self.table.setRangeSelected(QTableWidgetSelectionRange(currentTableItem.row(), 0, currentTableItem.row(), self.table.columnCount() - 1), True)
    
    @pyqtSlot()
    def cancel_on_click(self):
        self.close()
        
    @pyqtSlot()
    def play_on_click(self):
        print(self.album.title)         
        self.main.player.pause()
        self.main.playqueue.clear()        
        if not self.table.selectedItems():
            self.main.playqueue.add_album(self.album, True)
            return
        files = [item.data(Qt.UserRole) for item in self.table.selectedItems() if item.column() == 2]
        print(files)
        self.main.playqueue.add_files(files, True)
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
        self.host_input.setMaximumWidth(300)

        self.port_label = QLabel("Port: ", self)
        self.port_input = QLineEdit(str(main.config['port']), self)
        self.port_input.setMaximumWidth(300)
        
        self.volume_label = QLabel("Default Volume: ", self)
        self.volume_input = QLineEdit(str(main.config['volume']), self)
        self.volume_input.setMaximumWidth(300)

        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.cancel_on_click)
                
        self.ok_button = QPushButton('Ok', self)
        self.ok_button.clicked.connect(self.ok_on_click)
        
        self.layout = QGridLayout()
        self.layout.addWidget(self.host_label, 0, 0)
        self.layout.addWidget(self.host_input, 0, 1)
        self.layout.addWidget(self.port_label, 1, 0)
        self.layout.addWidget(self.port_input, 1, 1)
        self.layout.addWidget(self.volume_label, 2, 0)
        self.layout.addWidget(self.volume_input, 2, 1)
        self.layout.addWidget(self.cancel_button, 3, 0)
        self.layout.addWidget(self.ok_button, 3, 1)
        
        self.setLayout(self.layout) 
        self.show()
        
    @pyqtSlot()
    def cancel_on_click(self):
        self.close()
        
    @pyqtSlot()
    def ok_on_click(self):
        self.main.config['host'] = self.host_input.text().strip()
        self.main.config['port'] = int(self.port_input.text().strip())
        self.main.config['volume'] = int(self.volume_input.text().strip())
        self.main.save_config()
        self.main.initMPD()
        self.close()

       
    
class AsyncPlayQueue(object):
    def __init__(self, client, lock):
        self.client = client
        self.base = PlayQueue(client)
        self.lock = lock
                                
    def add_albums(self, albums, play=False, callback=None):
        run_async_mutex(self.lock, callback, self.base.add_albums, albums, play)

    def handlerFunctionClosure(self, name):
        def atomic_function_handler(*args, **kwargs):
            self.lock.lock()
            print("Lock for doing %r" % name)
            result = getattr(self.base, name)(*args, **kwargs)
            self.lock.unlock()
            print("Unlock for doing %r" % name)
            return result
        return atomic_function_handler
        
    def __getattr__(self, name):
        if name == "add_albums":
            return self.add_albums
        return self.handlerFunctionClosure(name)
        
        
class AsyncPlayer(object):
    def __init__(self, client, lock):
        self.base = Player(client)
        self.lock = lock
        
    def monitor(self, callback):
        run_loop(-1, callback, self.base.idle, "player")
    
    def handlerFunctionClosure(self, name):
        def atomic_function_handler(*args, **kwargs):
            self.lock.lock()
            print("Lock for doing %r" % name)
            result = getattr(self.base, name)(*args, **kwargs)
            self.lock.unlock()
            print("Unlock for doing %r" % name)
            return result
        return atomic_function_handler
        
    def __getattr__(self, name):
        if name == 'monitor':
            return self.monitor
        elif name == 'noidle':
            return self.base.noidle
        return self.handlerFunctionClosure(name)
 
class TableItem(QTableWidgetItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(self.flags() ^ Qt.ItemIsEditable)  #  Read only
    
    def enterEvent(self, QEvent):
        pass
        
    def leaveEnter(self, QEvent):
        pass
        
        
class App(QWidget): 
    def __init__(self):
        super().__init__()
        self.title = 'MPD Player with Expert Knowledge-based Music Recommendation'
        self.left = 0
        self.top = 0
        self.width = 1024
        self.height = 768
        self.log_file = "log.txt"

        self.initUI()
        self.load_config()
        try:
            self.initMPD()
            run_async(self.initData, self.initLibrary)
        except:
            self.loading_widget.setText("Fail to load the music library.\nCheck the setting of your MPD server in the Options menu and restart this player.")
            #self.popup_configuration()
        
    def __del__(self):
        self.mpd_server.close()
        self.mpd_server.disconnect()    
        
    def load_config(self):
        try:
            with open("config.json") as fin:
                self.config = json.load(fin)            
        except:
            self.config = {'host': 'localhost', 'port': 6600, 'volume': 100}
            
    def save_config(self):
        with open("config.json", "w") as fout:
            json.dump(self.config, fout)
        
    def initMPD(self):
        self.mpd_client_playqueue = connect_server(self.config['host'], self.config['port'])
        self.mpd_client_player = connect_server(self.config['host'], self.config['port'])
        self.mpd_client_monitor = connect_server(self.config['host'], self.config['port'])
    
    def initLibrary(self):
        self.mpd_mutex = QMutex()
        self.music_lib = Library(self.mpd_client_player, update=False)
        self.playqueue = AsyncPlayQueue(self.mpd_client_playqueue, self.mpd_mutex)
        self.player = Player(self.mpd_client_player)
        self.player.setvol(self.config['volume'])
        self.monitor = AsyncPlayer(self.mpd_client_monitor, None)
    
    def initData(self, results=None):
        collection = self.music_lib.list_latest_albums(10000000)
        self.updateAlbumTable(collection)
        self.updatePlaylist()
        self.updateRecommendation(collection)
#        self.playing_time = 0
#        self.playing = False
        
        self.update_status()
        self.update_local_info()
        
        #   Create Independent server for monitoring.
        self.monitor.monitor(self.update_status)
        
        self.local_updator = QTimer(self)
        self.local_updator.timeout.connect(self.update_local_info)
        self.local_updator.start(1000)
        
        self.stacked_tab.setCurrentIndex(1)
        
        
    def setPlaying(self, playing):
        self.playing = playing
        if playing:
            self.play_button.setChecked(True)
            self.play_button.setText('Pause')
        else:
            self.play_button.setChecked(False)
            self.play_button.setText('Play')
           
        
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
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'misc', 'icon.png')))
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
        
        self.stacked_tab = QStackedWidget()
        self.loading_widget = QLineEdit("Loading...", self)
        self.loading_widget.setAlignment(Qt.AlignCenter)
        self.stacked_tab.addWidget(self.loading_widget)
        self.stacked_tab.addWidget(self.albumTable)
                
        self.recommendation = createRecommendationGrid()
                
        self.tabs = QTabWidget()
        self.tabs.addTab(self.stacked_tab, "Albums")
        self.tabs.addTab(self.playlist, "Playlist")
        self.tabs.addTab(self.recommendation, "Recommendation")
        
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
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.play_on_click)
               
        self.infobox = QLineEdit("", self)
        self.infobox.setReadOnly(True)
        
        self.time_info = QLabel("", self)
        
        self.seek_slider = QSlider(Qt.Horizontal, self)
        self.seek_slider.setMaximumWidth(120)
        self.seek_slider.sliderMoved.connect(self.slider_moved)
        
        self.search_box = QLineEdit("", self)
        self.search_box.setMaximumWidth(120)
        self.search_box.returnPressed.connect(self.search_box_entered)
        self.search_box.textChanged.connect(self.search_button_reset)
        self.search_button = QPushButton('Search', self)
        self.search_button.clicked.connect(self.search_on_click)
                
        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setMaximumWidth(32)
        #self.volume_slider.setMaximumHeight(24)
        self.volume_slider.setMinimum(0)            
        self.volume_slider.setMaximum(100) 
        self.volume_slider.setToolTip("Volume")
        self.volume_slider.sliderMoved.connect(self.volume_change)
        
        layout = QHBoxLayout()
        layout.addWidget(self.play_button)
        layout.addWidget(self.infobox)
        layout.addWidget(self.seek_slider)
        layout.addWidget(self.time_info)
        layout.addWidget(self.search_box)
        layout.addWidget(self.search_button)
        layout.addWidget(self.volume_slider)
        
        self.controlPanel = QGroupBox()    
        self.controlPanel.setMaximumHeight(60)
        self.controlPanel.setLayout(layout)

    @pyqtSlot()
    def playlist_on_click(self):
        row = self.playlist.currentRow()
        songid = self.playlist.item(row, 2).data(Qt.UserRole)
        print(songid)
        try:
            self.player.playid(songid)
        except:
            self.handle_error()

    @pyqtSlot()       
    def update_local_info(self):
        if self.playing:
            self.playing_time += 1
            self.time_info.setText("%d/%d" % (self.playing_time, self.track_time))
            self.seek_slider.setMinimum(0)            
            self.seek_slider.setMaximum(self.track_time)
            self.seek_slider.setValue(self.playing_time)
        else:
            self.infobox.setText("")
            self.time_info.setText("")
            self.seek_slider.setValue(0)
                
    @pyqtSlot(object)
    def update_status(self, changes=None):
        print("Changes:")
        print(changes)
        track = self.playqueue.get_current_song()        
        status = self.player.status()
        if track and status and 'album' in track and 'time' in status:
            self.infobox.setText("%s: %d-%d %s %s" % (track['album'], int(track['disc']), int(track['track']), track['title'], track['artist']))
            self.playing_time = int(status['time'].split(":")[:-1][0])
            self.track_time = int(track['time'])
            if status['state'] == 'play':
                self.setPlaying(True)
            else:
                self.setPlaying(False)
            
            #   Highlight the playing track in the playlist.
            self.playlist.setRangeSelected(QTableWidgetSelectionRange(0, 0, self.playlist.rowCount() - 1, self.playlist.columnCount() - 1), False)
            self.playlist.setRangeSelected(QTableWidgetSelectionRange(int(track['pos']), 0, int(track['pos']), self.playlist.columnCount() - 1), True)
            self.volume_slider.setValue(int(status['volume']))
            self.volume_slider.setMinimum(0)            
            self.volume_slider.setMaximum(100) 
            self.volume_slider.setToolTip("Volume: " + status['volume'])
        else:
            self.infobox.setText("")
            self.time_info.setText("")
            self.setPlaying(False)
            self.seek_slider.setValue(0)
            
    @pyqtSlot()
    def slider_moved(self):
        self.player.seek(self.seek_slider.value())
            
    @pyqtSlot()
    def volume_change(self):
        self.player.setvol(self.volume_slider.value())
        self.volume_slider.setToolTip("Volume: " + str(self.volume_slider.value()))
            
    @pyqtSlot()
    def play_on_click(self):
        try:
            if self.playing:
                self.setPlaying(False)
                self.player.pause()
            else:
                self.setPlaying(True)
                self.player.play()
        except:
            self.handle_error()
            
    def handle_error(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Fail to connect the MPD player")
        msg.setInformativeText("There are something wrong about the connection with the player. Click OK to reload the player.")
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.buttonClicked.connect(self.initMPD)
        retval = msg.exec_()
        print("value of pressed message box button:", retval)

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
        def post_process():
            self.updateAlbumTable(self.music_lib.list_latest_albums(10000000))  
            self.stacked_tab.setCurrentIndex(1)
        
        def call_rebuild():
            self.music_lib = Library(self.mpd_client_playqueue, update=True)
            
        self.stacked_tab.setCurrentIndex(0)
        run_async_mutex(self.mpd_mutex, post_process, call_rebuild)
        
    @pyqtSlot()
    def search_button_reset(self):
        if self.search_button.text() == 'Clean':
            self.search_button.setText('Search')

    def search(self):
        if self.search_button.text() == 'Clean':
            query = ""
            self.search_button.setText('Search')
            self.search_box.setText('')
        else:
            query = self.search_box.text().strip()
        print(query)
        if not query:
            albums = self.music_lib.list_latest_albums(10000000)
        else:
            albums = self.music_lib.search(query.split())
            self.search_button.setText('Clean')
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
            title = TableItem(albums[i].title)
            title.setData(Qt.UserRole, albums[i].album_id)
            self.albumTable.setItem(i, 0, title)
            self.albumTable.setItem(i, 1, TableItem(albums[i].artist))
            self.albumTable.setItem(i, 4, TableItem(albums[i].last_modified[:10]))
        self.albumTable.move(0,0)
        
        self.sorted_order = Qt.DescendingOrder
        self.sorted_column = 2
        self.albumTable.sortItems(self.sorted_column, self.sorted_order)
        self.updateStatusBar(albums)
        
    def updatePlaylist(self):
        """'file': 'file:/disk2/share/Music/Music/Leif Ove Andsnes/Sibelius/05 Sibelius_ Kyllikki, Op. 41 - 3. C.m4a', 
        'last-modified': '2018-12-21T13:57:59Z', 
        'time': '175', 'artist': 'Leif Ove Andsnes', 'albumartist': 'Leif Ove Andsnes', 'artistsort': 'Leif Ove Andsnes', 'albumartistsort': 'Leif Ove Andsnes', 'album': 'Sibelius', 'title': 'Sibelius: Kyllikki, Op. 41 - 3. Commodo', 'track': '5', 'date': '2017', 'genre': 'Classical', 'disc': '1', 'pos': '4', 'id': '46227'}"""
        updateTrackTable(self.playlist, self.playqueue.list(), 'id')
        self.update_status()
#        self.albumTable.doubleClicked.connect(self.item_on_double_click)
#        self.playlist.clicked.connect(self.item_on_click)           
       
        
    def updateRecommendation(self, collection):
        table = self.recommendation
        items = get_recommendation_list(collection, 0)["album"]
     
        table.setRowCount((len(items) + 2) // 3)
        for idx, data in enumerate(items):
            img = QPixmap(data['cover_path'])
            cover_item = TableItem("")
            cover_item.setTextAlignment(Qt.AlignCenter)
            cover_item.setData(Qt.DecorationRole, img.scaled(140, 140, Qt.KeepAspectRatio))

            info = TableItem("%s\nBy %s\n%s, %s\nAMG Rating: %s" % (
                data['title'], data['artist'], data['label'], data['year'], data['rating']))
            info.setData(Qt.UserRole, data["link"])
            row = idx // 3
            col = (idx % 3) * 3
            table.setItem(row, col, cover_item)
            table.setItem(row, col + 1, info) 
            if col == 0:
                table.setRowHeight(row, 150)
                table.setItem(row, 2, TableItem(""))
                table.setItem(row, 5, TableItem(""))
        table.move(0,0)
        
    def createAlbumTable(self):
        # Create table
        self.albumTable = QTableWidget()
        self.albumTable.setRowCount(0)
        self.albumTable.setColumnCount(5)
        self.albumTable.setHorizontalHeaderLabels(["Title", "Aritst", "Genre", "Rating", "Last Modified"])
        header = self.albumTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.sectionClicked.connect(self.header_on_click)      
        
        row = self.albumTable.verticalHeader()
        row.sectionClicked.connect(self.row_on_click)
        
        # table selection change
        self.albumTable.doubleClicked.connect(self.item_on_double_click)
        self.albumTable.clicked.connect(self.item_on_click)
    
    @pyqtSlot()
    def item_on_click(self):
        row = self.albumTable.currentRow()
        self.albumTable.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, self.albumTable.columnCount() - 1), True)          

    @pyqtSlot()
    def item_on_double_click(self):
        row = self.albumTable.currentRow()
        self.albumTable.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, self.albumTable.columnCount() - 1), True)          
        self.popup_album()
    
    def popup_album(self):
        row = self.albumTable.currentRow()
        album_id = self.albumTable.item(row, 0).data(Qt.UserRole)
        album = self.music_lib.get_album(album_id)
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
            try:
                self.player.play()
            except:
                self.handle_error()
            return
        album_ids = set([item.data(Qt.UserRole) for item in self.albumTable.selectedItems() if item.column() == 0])
        print(album_ids)
        self.player.pause()
        self.playqueue.clear()
        albums = []
        for album_id in album_ids:
            albums.append(self.music_lib.get_album(album_id))

        print("Adding album")
        self.playqueue.add_albums(albums, True, self.updatePlaylist)
        print("Job sent")
        with open(self.log_file, "a", encoding="utf8") as fout:
            for album in albums:
                for track in album.tracks:
                    fout.write("%s\t%s\n" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), track['file']))
                    
    def closeEvent(self, event):
        print("Closing window")
        remove_threads()
        self.monitor.noidle()
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
    
