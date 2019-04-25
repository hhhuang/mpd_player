import json
import os
import random
import re
import time

import requests
import shutil

def get_cover_filename(link):
    m = re.search("www\.allmusic\.com\/(.+)$", link)
    if m:
        return m.group(1).replace("/", "-") + ".jpg"
    raise ValueError

def download_cover(link, cover_link):
    if not cover_link:
        return None 
    filename = get_cover_filename(link)
    cover_path = os.path.join(os.path.dirname(__file__), 'covers', filename)
    if os.path.isfile(cover_path):
        return cover_path
    time.sleep(random.randint(1, 5))
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
    headers = { 'User-Agent' : user_agent }  
    res = requests.get(cover_link, headers=headers, stream=True, verify=False)
    if res.status_code == 200:
        with open(cover_path, "wb") as fout:
            shutil.copyfileobj(res.raw, fout)
        return cover_path
    return None

def get_cover_path(link, cover_link):
    path = download_cover(link, cover_link)
    if not path:
        path = os.path.join(os.path.dirname(__file__), 'covers', 'default.png')
    return path

def load_albums():
    albums = {}
    with open(os.path.join(os.path.dirname(__file__), "data", "artists.jsons")) as fin:
        for line in fin:
            data = json.loads(line)
            if not data or 'name' not in data:
                print("skip")
                continue
            for album in data['albums']:
                album['artist'] = data['name']
                if album['rating'].startswith('rating-allmusic-'):
                    stars = u"\u2605" * ((int(album['rating'][-1]) + 1) // 2)
                    if (int(album['rating'][-1]) + 1) % 2 == 1:
                        stars += u"\u2606"
                    album['rating'] = stars
                else:
                    album['rating'] = "N/A"
                albums[album['link']] = album
    return albums

if __name__ == "__main__":
    print(load_albums())
