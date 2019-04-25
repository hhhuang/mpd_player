import hashlib
import json
import os
import random
import re
import requests
import time

from collections import deque

from bs4 import BeautifulSoup

def get_str_hash(s):
    hash_obj = hashlib.sha1(s.encode('utf8'))
    return hash_obj.hexdigest()


def fix_link(url):
    if url[0] == '/':
        return "https://www.allmusic.com" + url
    return url

def open_url(url):
    url = fix_link(url)
    cache_path = os.path.join(os.path.dirname(__file__), 'cache', get_str_hash(url))
    if os.path.isfile(cache_path):
        print("Open cached file")
        with open(cache_path, encoding='utf8') as fin:
            return fin.read()
    print("Crawl from the internet: %s" % url)
    time.sleep(random.randint(1, 5))
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
    headers = { 'User-Agent' : user_agent }  
    res = requests.get(url, headers=headers)
    with open(cache_path, "w", encoding='utf8') as fout:
        fout.write(res.text)
    return res.text


def find_class_all(soup, unit, cls):
    cls = cls.split(" ")
    for u in soup.find_all(unit):
        if 'class' in u.attrs and u.attrs['class'] == cls:
            yield u


def find_class(soup, unit, cls):
    for u in find_class_all(soup, unit, cls):
        return u


def extract_basic_info(url):
    data = {}
    print(url)
    src = open_url(url)
    soup = BeautifulSoup(src, 'html.parser')
    if not find_class(soup, 'h1', 'artist-name'):
        return None
    data['name'] = find_class(soup, 'h1', 'artist-name').text.strip()
    data['link'] = fix_link(url)
    try:
        data['portrait_link'] = find_class(soup, 'div', 'artist-image').find_all('img')[0].get('src')
    except:
        data['portrait_link'] = None 
    fields = ['active-dates', 'birth']
    for field in fields:
        if not find_class(soup, 'div', field):
            continue
        data[field] = find_class(soup, 'div', field).find_all('div')[0].text.strip()
        data[field] = " ".join([tok for tok in data[field].split(" ") if tok != ""])

    data['styles'] = []
    if find_class(soup, 'div', 'styles'):
        for style in find_class(soup, 'div', 'styles').find_all('div')[0].find_all('a'):
            data['styles'].append((fix_link(style.get('href')), style.text.strip()))

    data['genre'] = []
    if find_class(soup, 'div', 'genre'):
        for genre in find_class(soup, 'div', 'genre').find_all('div')[0].find_all('a'):
            data['genre'].append((fix_link(genre.get('href')), genre.text.strip()))

    data['group_members'] = []
    if find_class(soup, 'div', 'group-members'):
        for member in find_class(soup, 'div', 'group-members').find_all('div')[0].find_all('a'):
            data['group_members'].append((fix_link(member.get('href')), member.text.strip()))

    data['member_of'] = []
    if find_class(soup, 'div', 'member-of'):
        for member in find_class(soup, 'div', 'member-of').find_all('div')[0].find_all('a'):
            data['member_of'].append((fix_link(member.get('href')), member.text.strip()))

    data['moods'] = []
    if find_class(soup, 'section', 'moods'):
        for mood in find_class(soup, 'section', 'moods').find_all('a'):
            data['moods'].append((fix_link(mood.get('href')), mood.text.strip()))

    data['themes'] = []
    if find_class(soup, 'section', 'themes'):
        for mood in find_class(soup, 'section', 'themes').find_all('a'):
            data['themes'].append((fix_link(mood.get('href')), mood.text.strip()))
    return data


def crawl_related(url):
    data = {}
    print(url)
    src = open_url(url)
    soup = BeautifulSoup(src, 'html.parser')
    for section in ['related similars', 'related influencers', 'related followers', 'related associatedwith', 'related collaboratorwith']:
        data[section.split(" ")[1]] = []
        if find_class(soup, 'section', section):
            for a in find_class(soup, 'section', section).find_all('a'):
                data[section.split(" ")[1]].append((fix_link(a.get('href')), a.text.strip()))
    return data

def crawl_albums(url):
    data = {}
    print(url)
    src = open_url(url)
    soup = BeautifulSoup(src, 'html.parser')
    data['albums'] = []
    if not soup.find_all('tbody'):
        return data
    for row in soup.find_all('tbody')[0].find_all('tr'):
        album = {}
        try:  
            album['cover_link'] = find_class(row, 'td', 'cover').find_all('img')[0].get('data-original')
        except:
            album['cover_link'] = None
        album['link'] = fix_link(find_class(row, 'td', 'title').find_all('a')[0].get('href'))
        album['year'] = find_class(row, 'td', 'year').text.strip()
        album['title'] = find_class(row, 'td', 'title').text.strip()
        album['label'] = find_class(row, 'td', 'label').text.strip()
        album['rating'] = find_class(row, 'td', 'all-rating').find_all('div')[0].attrs['class'][1]
        data['albums'].append(album)
    return data

def crawl_artist(base_url):
    artist = extract_basic_info(base_url)
    if artist is None:
        return None
    artist.update(crawl_related(base_url + '/related'))
    artist.update(crawl_albums(base_url + '/discography'))
    return artist
   
def crawl_all():
    fout = open(os.path.join(os.path.dirname(__file__), "data", "artists.jsons"), "w")
    #root = 'https://www.allmusic.com/artist/the-velvet-underground-mn0000840402'
    #root = 'https://www.allmusic.com/artist/the-velvet-underground-mn0000840402'
    #root = 'https://www.allmusic.com/artist/bing-crosby-mn0000094252'
    root = 'https://www.allmusic.com/artist/the-beatles-mn0000754032'
    crawled_artists = set()

    queue = deque()
    queue.append(root)
    while len(queue) > 0:
        artist = queue.popleft()
        if artist is None:
            continue
        if artist in crawled_artists:
            continue
        data = crawl_artist(artist)
        fout.write(json.dumps(data) + "\n")
        crawled_artists.add(artist)
        for a, _ in set(data['similars'] + data['influencers'] 
            + data['followers'] + data['associatedwith'] + data['collaboratorwith']):
            if a not in crawled_artists:
                queue.append(a)
    
if __name__ == "__main__":
    crawl_all()

