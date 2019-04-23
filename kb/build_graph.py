from collections import defaultdict, Counter
import json
import os

import knowledge_embedding

inv_idx = defaultdict(list)
entities = []
track_table = {}

def get_indexes(text):
    return set([t for t in text.lower().split() if t != 'the'])

class Entity:
    def __init__(self, name, entity_type):
        self.name = name
        self.entity_type = entity_type
        self.related = defaultdict(set)

    def add_relation(self, entity, relation_type):
        if type(entity) != Entity:
            raise TypeError
        self.related[relation_type].add(entity)

    def __str__(self):
        return "%s_(%s)" % (self.name.replace(" ", "_"), self.entity_type)

    def __repr__(self):
        return "(%s, %s, %d)" % (self.name, self.entity_type, len(self.related))

    def get_indexes(self):
        return get_indexes(self.name)

def load_allmusic():
    valid_artists = set()
    with open(os.path.join(os.path.dirname(__file__), "data", "artists.jsons")) as fin:
        for line in fin:
            data = json.loads(line)
            if not data or 'name' not in data:
                print("skip")
                continue
            valid_artists.add(data['name'])
    
    with open(os.path.join(os.path.dirname(__file__), "data", "artists.jsons")) as fin:
        for line in fin:
            data = json.loads(line)
            if not data or 'name' not in data:
                print("skip")
                continue
            artist = Entity(data['name'], 'artist')
            for entry in data['albums']:
                album = Entity(entry['title'], 'album')
                artist.add_relation(album, 'albums')
            for relation in ['influencers', 'followers', 'collaboratorwith', 'group_members', 'associatedwith', 'similars', 'themes', 'moods', 'styles', 'genre']:
                for entry in data[relation]:
                    if relation in ['influencers', 'followers', 'collaboratorwith', 'group_members', 'associatedwith', 'similars'] and entry[1] in valid_artists:
                        e = Entity(entry[1], 'artist')
                    elif relation in ['themes', 'moods', 'styles']:
                        e = Entity(entry[1], relation[:-1])
                    elif relation in ['genre']:
                        e = Entity(entry[1], relation)
                    else:
                        continue
                    artist.add_relation(e, relation)
            for idx in artist.get_indexes():
                inv_idx[idx].append(artist) 
            entities.append(artist)

def match(tokens):
    matched = Counter()
    for tok in tokens:
        if tok in inv_idx:
            for artist in inv_idx[tok]:
                matched[artist] += 1
    return [k for k, _ in matched.most_common(5)]

def find_entity(artist_name, album_name):
    artist_tokens = artist_name.lower().replace("_", "").split()
    feasible_artists = match(artist_tokens)
    for artist in feasible_artists:
        for album in artist.related['albums']:
            if album.name.lower().strip() == album_name.lower().strip():
                return artist, album

    for artist in feasible_artists:
        if artist.name.lower().strip() == artist_name.lower().strip():
            return artist, None
    return None, None

def load_logs(before=9999):
    with open(os.path.join(os.path.dirname(__file__), os.pardir, "log.txt")) as fin:
        for line in fin:
            if not line or int(line.strip()[:4]) >= before:
                continue
            f = line.strip()[20:]
            if f not in track_table:
                continue
            artist, album = track_table[f]
            if artist:
                artist.add_relation(Entity('User', 'user'), 'listened')
            if album:
                album.add_relation(Entity('User', 'user'), 'listened')
            if artist and album:
                print("%r %r is found" % (artist, album))
            elif artist:
                print("%r is found" % artist)

def load_library(before=9999):
    with open(os.path.join(os.path.dirname(__file__), os.pardir, "library.json")) as fin:
        lib = json.load(fin)
    for entry in lib:
        if 'file' not in entry:
            continue
        try:
           if int(entry['last-modified'][:4]) >= before:
               continue
        except:
            print(entry)
            quit()
        artist, album = find_entity(entry['albumartist'], entry['album'])
        if artist:
            track_table[entry['file']] = (artist, album)
            artist.add_relation(Entity('User', 'user'), 'bought')
            if album:
                album.add_relation(Entity('User', 'user'), 'bought')
                print("%s, %s is found in %r %r" % (entry['albumartist'], entry['album'], artist, album))
            else:
                print("%s is found in %r" % (entry['albumartist'], artist))

entity_ids = {}
relation_ids = {}

def lookup_id(key, table):
    if key not in table:
        table[key] = len(table)
    return table[key]

def lookup_relation_id(rel):
    return lookup_id(rel, relation_ids)

def lookup_entity_id(entity):
    return lookup_id(str(entity), entity_ids)

def train_kb(before=9999, folder=None):
    if folder is None:
        folder = os.path.join(os.path.dirname(__file__), "data")
    load_allmusic()
    load_library(before)
    load_logs(before)
    bought_artists = set()
    bought_albums = set()
    listened_artists = set()
    listened_albums = set()
    for entry in entities:
        if 'bought' in entry.related:
            bought_artists.add(entry)
        if 'listened' in entry.related:
            listened_artists.add(entry)
        if 'albums' in entry.related:
            for album in entry.related['albums']:
                if 'bought' in album.related:
                    bought_albums.add(album)
                if 'listened' in album.related:
                    listened_albums.add(album)

    print("Number of bought artists: %d" % len(bought_artists))
    print("Number of bought albums: %d" % len(bought_albums))
    triples = []
    type_counts = defaultdict(Counter) 
    for entry in entities:
        e1 = lookup_entity_id(entry)
        type_counts[entry.entity_type][entry.name] += 1
        for rel in entry.related:
            r = lookup_relation_id(rel)
            for entry2 in entry.related[rel]:
                e2 = lookup_entity_id(entry2)
                type_counts[entry2.entity_type][entry2.name] += 1
                triples.append((e1, e2, r))
    for t in type_counts:
        print("%s\t%d" % (t, len(type_counts[t])))
        print(type_counts[t].most_common(5))

    with open(os.path.join(folder, "train2id.txt"), "w") as fout:
        fout.write("%d\n" % len(triples))
        for triple in triples:
            fout.write("%d\t%d\t%d\n" % triple)
    with open(os.path.join(folder, "entity2id.txt"), "w") as fout:
        fout.write("%d\n" % len(entity_ids))
        for entity in entity_ids:
            fout.write("%s\t%d\n" % (entity, entity_ids[entity]))
    with open(os.path.join(folder, "relation2id.txt"), "w") as fout:
        fout.write("%d\n" % len(relation_ids))
        for rel in relation_ids:
            fout.write("%s\t%d\n" % (rel, relation_ids[rel]))
    knowledge_embedding.train_kb(folder)
 

if __name__ == "__main__":
    train_kb()
    quit()
    #   The following part is used for training the kb.
    train_kb(2015)
    
    # Prepare test data
    load_library()
    load_logs()
    
    test_bought_artist_triples = []
    test_bought_album_triples = []
    
    for entry in entities:
        if 'bought' in entry.related and entry not in bought_artists:
            for e2 in entry.related['bought']:
                test_bought_artist_triples.append((entry, e2, 'bought'))
                break
        """if 'listened' in entry.related and entry not in listened_artists:
            for e2 in entry.related['listened']:
                test_triples.append((entry, e2, 'listened'))"""
        if 'albums' in entry.related:
            for album in entry.related['albums']:
                if 'bought' in album.related and album not in bought_albums:
                    for e2 in album.related['bought']:
                        test_bought_album_triples.append((album, e2, 'bought'))
                        break
                """if 'listened' in album.related and album not in listened_albums:
                    for e2 in album.related['listened']:
                        test_triples.append((album, e2, 'listened'))"""
    print(len(test_bought_artist_triples))
    print(len(test_bought_album_triples))
    import random

    with open("data/test_bought_artist.txt", "w") as fout:
        for triple in test_bought_artist_triples:
            questions = [triple]
            while len(questions) < 50:
                entity = random.choice(entities)
                if entity not in bought_artists: 
                    questions.append((entity, triple[1], triple[2]))
            for q in questions:
                fout.write("%d\t%d\t%d\n" % (lookup_entity_id(q[0]), lookup_entity_id(q[1]), lookup_relation_id(q[2])))
    with open("data/test_bought_album.txt", "w") as fout:
        for triple in test_bought_album_triples:
            questions = [triple]
            while len(questions) < 50:
                entity = random.choice(entities)
                if len(entity.related['albums']) > 0:
                    album = random.choice(list(entity.related['albums']))
                    if album not in bought_albums: 
                        questions.append((album, triple[1], triple[2]))
            for q in questions:
                fout.write("%d\t%d\t%d\n" % (lookup_entity_id(q[0]), lookup_entity_id(q[1]), lookup_relation_id(q[2])))
