# MPD Player with Expert Knowledge-based Music Recommendation

This is an audiophile music player based on the [MPD](https://www.musicpd.org) protocol. 
The player will suggest the relevant albums and artists to the user based the playback log. 
A knowledge base built on the top of [All Music Guide](https://www.allmusic.com) is employed to peformance the recommendation as a task of knowledge base completion. 

Technical information about the music recommendation is available [here](https://github.com/hhhuang/mpd_player/blob/master/misc/paper.pdf) (submitted to the demo track of IJCAI 2019).

## Environment Requirement
* Python3
* Operating system: Windows/Mac/Linux and so on. The code has been verified on Windows 10 and Mac OS Mojave.
* A collection of audio files that is manipulated by an MPD server. [More information of the setup of the MPD server](https://wiki.archlinux.org/index.php/Music_Player_Daemon).   
* For training yourself own personalized knowledge base, 
  build the [Open Knowledge Embedding](https://github.com/thunlp/OpenKE) toolkit in the folder ```kb/OpenKE```. C++ is required to build OpenKE.
  ```
  cd kb/OpenKE
  sh make.sh
  ```

## Setup

### Install related packages

```pip3 install -r requirements.txt```

### Start the player

```python3 mpd_player_gui.py```
  
A failure message will be shown if the default MPD setting does not work.
  
![Failure](https://github.com/hhhuang/mpd_player/blob/master/misc/fail.png?raw=true)

### Assign the MPD music server and restart the player

![Configuration](https://github.com/hhhuang/mpd_player/blob/master/misc/setting.png?raw=true)

The server can also be set up manually in the file ```config.json``` as follows.

```{"host": "192.168.0.1", "port": 6600, "volume": 100}```

### Rebuild the library for your music collection
It takes some time depending on the size of your music collection.

### Play an album
![GUI](https://github.com/hhhuang/mpd_player/blob/master/misc/player_gui.png?raw=true)

