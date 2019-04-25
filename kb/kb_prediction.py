import json
import os
import re

import numpy

from kb import database

entity_embeddings = []
relation_embeddings = []

def predict(h, t, r):
    return abs(h + r - t).mean()

def load_embeddings():
    global entity_embeddings 
    global relation_embeddings
    with open(os.path.join(os.path.dirname(__file__), "data", "embedding.vec.json")) as fin:
        data = json.load(fin)
        entity_embeddings = data['ent_embeddings']
        relation_embeddings = data['rel_embeddings']
        print(len(entity_embeddings))
        print(len(relation_embeddings))

def evaluate(num_options):
    load_embeddings()
    correct = 0
    mrr = 0
    with open(os.path.join(os.path.dirname(__file__), "data", "test_bought_album.txt")) as fin:
        cnt = 0
        scores = []
        for line in fin:
            row = line.strip().split()
            e1 = numpy.array(entity_embeddings[int(row[0])])
            e2 = numpy.array(entity_embeddings[int(row[1])])
            r = numpy.array(relation_embeddings[int(row[2])])
            s = predict(e1, e2, r)
            scores.append((s, cnt % num_options))
            if len(scores) >= num_options:
                scores.sort()
                if scores[0][1] == 0:
                    correct += 1
                for i in range(len(scores)):
                    if scores[i][1] == 0:
                        mrr += 1.0 / (i + 1)
                        break
                print(scores)
                scores = []
            cnt += 1
        print("Accuracy: %f" % (correct / (cnt / num_options)), end="\t")
        print("MRR: %f" % (mrr / (cnt / num_options)))

def load_id_table(path):
    table = {}
    with open(path) as fin:
        for line in fin:
            row = line.strip().split()
            if len(row) == 2:
                table[int(row[1])] = row[0]
    return table

def load_entity_table():
    return load_id_table(os.path.join(os.path.dirname(__file__), "data", "entity2id.txt"))

def load_relation_table():
    return load_id_table(os.path.join(os.path.dirname(__file__), "data", "relation2id.txt"))

def recover_link(entity_name):
    """Recover the entity link given the entity name"""
    pos = entity_name.rfind("_(")
    if pos > 0:
        return entity_name[:pos]
    return entity_name

def top_list(entity_type):
    entities = load_entity_table()
    relations = load_relation_table()
    for idx, rel in relations.items():
        if rel == 'bought':
            target_rel_id = idx
            break
    else:
        print("No target relation is found.")
        quit()
    for idx, ent in entities.items():
        if ent == 'User_(user)':
            target_ent_id = idx
            break
    else:
        print("No user entity is found")
        quit()
    load_embeddings()
    data = []
    for eid, e_name in entities.items():
        try:
            e_type = re.search("www\.allmusic\.com\/([^\/]+)\/", e_name).group(1)
        except:
            continue
        if e_type == entity_type:
            score = predict(
                numpy.array(entity_embeddings[eid]), 
                numpy.array(entity_embeddings[target_ent_id]), 
                numpy.array(relation_embeddings[target_rel_id]))
            data.append((score, recover_link(e_name)))
    data.sort()
    return data

def get_recommendation_list(collection, num_items):
    results = {"album": []}
    albums = database.load_albums()
    for _, album_link in top_list("album")[:num_items]:
        if album_link not in albums:
            print(album_link + " is not found")
            continue
        data = albums[album_link]
        data['cover_path'] = database.get_cover_path(album_link, data['cover_link'])
        results['album'].append(data)
    return results

if __name__ == "__main__":
    print(top_list("artist")[:50])
    quit()
    evaluate(50)
    #print(top_list("album"))

