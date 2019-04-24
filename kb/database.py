import json
import os

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
