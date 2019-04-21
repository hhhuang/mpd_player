import mpd as musicpd
import json
import jsonpickle
import os.path
import heapq

from libs.collation import latin2ascii
#from os import environ

#environ['MPD_HOST'] = '192.168.11.235'
#environ['MPD_PORT'] = '6601'

def connect_server(host='localhost', port=6600):
    client = musicpd.MPDClient()       # create client object
    client.connect(host, port)                   # use MPD_HOST/MPD_PORT if set else
                                   #   test ${XDG_RUNTIME_DIR}/mpd/socket for existence
                                   #   fallback to localhost:6600
                                   # connect support host/port argument as well
    print(client.mpd_version)           # print the mpd version
    #print(client.listall())
#    print(client.lsinfo('file:/disk2/share/Music/Music/Sviatoslav Richter/Beethoven_ Rondos, Bagatelles_ Chopin_ E/08 Chopin_ Etude #3 In E, Op. 10_3,.m4a'))
    #print(album)
    return client
    
class Album(object):
    @classmethod
    def get_album_key(cls, file):
        """ Sample format: 
        "file": "file:/disk2/share/Music/Music/Walter Gieseking/Bach_ Partitas/1-06 Partita No.1 in B-flat, BWV 825.m4a", 
        "last-modified": "2017-11-29T15:42:37Z", 
        "time": "138", 
        "artist": "Walter Gieseking",
        "albumartist": "Walter Gieseking", 
        "artistsort": "Walter Gieseking", 
        "albumartistsort": "Walter Gieseking", 
        "album": "Bach: Partitas", 
        "title": "Partita No.1 in B-flat, BWV 825 - 6. Giga", 
        "track": "6",
        "date": "1950", 
        "genre": "Classical",
        "disc": "1"}"""
        rows = os.path.split(file['file'])
        return rows[0] + "/" + file['album']
        
    def __init__(self, album_id):
        self.album_key = None
        self.album_id = album_id
        self.tracks = []
        self.title = ""
        self.last_modified = ""
        self.artist = ""
        self.keywords = ""
    
    def add(self, track):
        key = Album.get_album_key(track)
        if not self.album_key:
            self.album_key = key
            self.title = track['album']
            self.last_modified = track['last-modified']
            self.artist = track['albumartist']
        elif self.album_key != key:
            raise ValueError('The album key %s does not match %s.' % (key, self.album_key))
        if 'disc' not in track:
            track['disc'] = 1
        else:
            track['disc'] = int(track['disc'])
        if 'track' not in track:
            track['track'] = 1
        else:
            track['track'] = int(track['track'])
        self.tracks.append(track)
        
    def match(self, keywords):
        for keyword in keywords:
            if latin2ascii(keyword.lower()) not in self.keywords:
                return False
        return True
                
    def complete(self):
        self.gen_keywords()
        self.sort_tracks()
    
    def sort_tracks(self):
        self.tracks.sort(key=lambda x: (x['disc'], x['track']))
    
    def gen_keywords(self):
        keywords = set([self.title.lower(), self.artist.lower()])
        for track in self.tracks:
            keywords.add(latin2ascii(track['title'].lower()))
            keywords.add(latin2ascii(track['artist'].lower()))
        self.keywords = " ".join(keywords)        
        
    def __cmp__(self, other):
        return cmp(self.last_modified, other.last_modified)
        
    
class Library(object):
    def __init__(self, client, update=False):
        self.client = client
        self.cache_path = "library.json"
        self.album_path = "albums.json"
        if update:
            self.update()
        self.build()
        """with open(self.album_path) as fin:
            self.albums = jsonpickle.decode(json.load(fin))
            print("Number of albums loaded: %d" % len(self.albums))"""
    
    def update(self):
        data = self.client.listallinfo()
        with open(self.cache_path, "w") as fout:
            json.dump(data, fout)
        
    def build(self):
        with open(self.cache_path) as fin:
            albums = self.build_albums(json.load(fin))
        with open(self.album_path, "w") as fout:
            json.dump(jsonpickle.encode(albums), fout)
        
    def build_albums(self, data):
        self.albums = {}
        self.album_lookup = []
        num_tracks = 0
        for entry in data:
            if 'file' not in entry:
                continue
            key = Album.get_album_key(entry)
            if key not in self.albums:
                self.albums[key] = Album(len(self.album_lookup))
                self.album_lookup.append(key)
            self.albums[key].add(entry)
            num_tracks += 1
        print("Number of albums: %d, Number of tracks: %d" % (len(self.albums), num_tracks))
        self.latest_albums = []
        for album in self.albums.values():
            album.complete()
            self.latest_albums.append((album.album_id, album.last_modified))
        self.latest_albums.sort(key=lambda x: x[1], reverse=True)
        #print(self.latest_albums)
        
    def get_album(self, album_id):
        return self.albums[self.album_lookup[album_id]]
    
    def list_latest_albums(self, size=20):
        albums = []
        for album_id, _ in self.latest_albums[:size]:
            albums.append(self.get_album(album_id))
        return albums
    
    def search(self, keywords):
        albums = []
        keywords = list(map(str.lower, keywords))
        for album in self.albums.values():
            if album.match(keywords):
                albums.append(album)
        return albums
        
    
class PlayQueue(object):
    def __init__(self, client):
        self.client = client
        
    def add_album(self, album, play=False):
        for track in album.tracks:
            self.client.add(track['file'])
            if play:
                self.client.play()
                play = False
        
    def add_albums(self, albums, play=False):
        print(self.client)
        for album in albums:
            for track in album.tracks:
                print("Adding: %s" % track['file'])
                self.client.add(track['file'])
                if play:
                    self.client.play()
                    play = False
         
    def add_files(self, files, play=False):
        for file in files:
            self.client.add(file)
            if play:
                self.client.play()
                play = False
                            
    def add_track(self, album, track):
        self.client.add(album.tracks[track - 1]['file'])
                    
    def clear(self):
        self.client.clear()
    
    def list(self):
        return self.client.playlistinfo()
        
    def get_current_song(self):
        return self.client.currentsong()
    
        
class Player(object):
    def __init__(self, client):
        self.client = client
        
    def play(self):
        self.client.play()
        
    def stop(self):
        self.client.stop()
        
    def pause(self):
        try:
            self.client.pause()
        except:
            pass
        
    def next(self):
        self.client.next()
    
    def previous(self):
        self.client.previous()
        
    def status(self):
        return self.client.status()
        
    def idle(self, *args, **kwargs):
        return self.client.idle(*args, **kwargs)
                       
    def noidle(self):
        return self.client.noidle()
        
    def seek(self, time):
        self.client.seekcur(time)
        
    def playid(self, songid):
        self.client.playid(songid)
        
    def setvol(self, vol):
        self.client.setvol(vol)
    
def show_list(albums):
    print("Number of albums: %d" % len(albums))
    for album in albums:
        print("%6d: %s %s" % (album.album_id, album.title, album.artist))
        
def show_album(album):
    print("%6d: %s %s" % (album.album_id, album.title, album.artist))
    for track in album.tracks:
        print("%2d:%3d - %s %s" % (track['disc'], track['track'], track['title'], track['artist']))

if __name__ == "__main__":
    client = connect_server('192.168.11.235', 6601)
    music_lib = Library(client, update=False)
    pq = PlayQueue(client)
    player = Player(client)

    pause = False
    while True:
        cmd = input()
        rows = cmd.split()
        cmd = rows[0]
        if cmd == 'q':
            break
        elif cmd == 'p':
            if len(rows) >= 2:
                pq.clear()
                if len(rows) == 2:
                    album = music_lib.get_album(int(rows[1]))
                    pq.add_album(album, True)
                    show_album(album)
                elif len(rows) == 3:
                    album = music_lib.get_album(int(rows[1]))
                    track = int(rows[2])
                    pq.add_track(album, track, True)
                    show_album(album)
            client.status()
        elif cmd == 's':
            player.pause()
        elif cmd == 'latest':
            size = int(rows[1]) if len(rows) == 2 else 20
            show_list(music_lib.list_latest_albums(size))
        elif cmd == 'search':
            show_list(music_lib.search(rows[1:]))
        elif cmd == 'v':
            show_album(music_lib.get_album(int(rows[1])))
        elif cmd == 'update':
            music_lib = Library(client, update=True)
        elif cmd == 'status':
            print(client.status())
            print(pq.get_current_song())
            for track in client.playlistinfo():
                print(track['file'])
        elif cmd == 'idle':
            print(player.idle())
        elif cmd == 'volume':
            player.setvol((int(rows[1])))
        else:
            print("Unknown command: %s" % cmd)

    client.close()                     # send the close command
    client.disconnect()                # disconnect from the server
