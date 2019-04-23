import json
import os

import numpy

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

def load_entity_table():
    entities = {}
    with open(os.path.join(os.path.dirname(__file__), "data", "entity2id.txt")) as fin:
        for line in fin:
            row = line.strip().split()
            if len(row) == 2:
                entities[int(row[1])] = row[0]
    return entities

def top_list(entity_type):
    entities = load_entity_table()
    load_embeddings()
    data = []
    for eid, e_name in entities.items():
        if e_name.endswith("(%s)" % entity_type):
            score = predict(
                numpy.array(entity_embeddings[eid]), 
                numpy.array(entity_embeddings[382]), 
                numpy.array(relation_embeddings[10]))
            data.append((score, e_name))
    data.sort()
    return data

if __name__ == "__main__":
    evaluate(50)
    #print(top_list("album"))

