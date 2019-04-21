import json
import sys

if len(sys.argv) == 3:
    key = sys.argv[2]
else:
    key = None

num_albums = 0
with open(sys.argv[1]) as fin:
    cnt = 0
    for line in fin:
        data = json.loads(line)
        cnt += 1
        if key is None:
            print("%d: %s" % (cnt, data["name"]))
            num_albums += len(data['albums'])
        elif data["name"].lower() == key.lower():
            for x in data:
                print(x)
                print(data[x])
            break
print(num_albums)
