# MPD Player with Expert Knowledge-based Music Recommendation

This is an audiophile music player based on the [MPD](https://www.musicpd.org) protocol. 
The player will suggest the relevant albums and artists to the user based the playback log. 
A knowledge base built on the top of [All Music Guide](https://www.allmusic.com) is employed to peformance the recommendation as a task of knowledge base completion. 

## Key Features
* Friendly with a large number of albums. The player has been tested with a collection more than 2,000 CDs.
* This player is album-oriented. All the tracks in the MPD server are reorganized into albums. Compared with individual tracks, album is a much more structural and meaningful unit for serious music lovers' critical listening. 
* Many MPD servers and renderers are built on low-power devices such as NAS and Raspberry Pi. To reduce the loading of these devices, all the loading are taken by the controller side (i.e. this player). This design philosophy results a slim, mimimal, somewhat slow player, but both server/renderer sides benefit from stability, lower jitter, and better sound quailty. 
* Psersonalized music recommendation based on the user's collection and playback log. A knowledge base built on the expert knowlegdge from All Music Guide is tightly integrated into this player. Technical information about the music recommendation is available [here](https://github.com/hhhuang/mpd_player/blob/master/misc/paper.pdf) (submitted to the demo track of IJCAI 2019).
The slides are [here](https://github.com/hhhuang/mpd_player/blob/master/misc/slides.pdf).

## Environment Requirement
* Python3
* Operating system: Windows/Mac/Linux and so on. The code has been verified on Windows 10 and Mac OS Mojave.
* A collection of audio files that is manipulated by an MPD server. [More information of the setup of the MPD server](https://wiki.archlinux.org/index.php/Music_Player_Daemon). An ideal setting is comprised of a standalone music server running the MPD server like [Forked-Daapd](http://ejurgensen.github.io/forked-daapd/), a standalone music renderer like a Hi-Fi DAC/Stream Player that supports MPD, and this player installed on another powerful desktop/laptop in the same LAN. 
* Build the [Open Knowledge Embedding](https://github.com/thunlp/OpenKE) toolkit in the folder ```kb/OpenKE```. A C++ compiler is required to build OpenKE.
  ```
  cd kb/OpenKE
  sh make.sh
  ```
  OpenKE is a submodule so you may need to checkout it manually if the folder is empty. 
  ```
  git submodule init
  git submodule update --recursive
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


## Recommendation
Based on your music collection and your playback log, a personalized recommendation list of albums to purchase is predicted.
The recommendation list takes a little time to render because the cover images are downloaded on the fly. 
![Recommendation](https://github.com/hhhuang/mpd_player/blob/master/misc/recommendation.png?raw=true)

## Known Issues under Improvement
* The procedure for cover image download will be performed in the background.
* The recommendation list will be updated regularly according to the change of user's music collection and playback log.
