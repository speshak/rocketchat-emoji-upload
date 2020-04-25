from pymongo import MongoClient
import gridfs
import time
import datetime
from bson.json_util import loads
import json
import yaml
import urllib2
import traceback
import sys

emoji_yaml_url = sys.argv[1]
mongo_server = 'localhost'

response = urllib2.urlopen(emoji_yaml_url)
emoji_yaml = yaml.load(response.read())

# load YAML into parsable list
emojis = emoji_yaml['emojis']


# create timestamp for entry into list for DB
ts = time.time()
ts = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')


# make connection to mongo
client = MongoClient(mongo_server)
db = client.rocketchat


# gridfs file uploader function
def gfs_fileuploader(name, content, url):
    custom_emoji = gridfs.GridFS(db, 'custom_emoji')
    opener = urllib2.build_opener()
    # change user agent to wget, for some reason CDN does not like urillib2
    opener.addheaders = [('User-Agent', 'Wget/1.19.1 (darwin16.6.0)')]
    urllib2.install_opener(opener)

    emoji_resp = opener.open(url)
    emoji_file = emoji_resp.read()

    with custom_emoji.new_file(
        _id=name,
        filename=name,
        content_type=content,
        alias=None) as fp:
        fp.write(emoji_file)


# download image files and make Array for DB entries
# declare array
new_emojis = []
for emoji in emojis:
    try:
        url = emoji['src']
        filename = url.split('/')
        file = filename[len(filename)-1]
        file = file.split('.')
        name = emoji['name']
        ext = file[1]
        new_file = name + '.' + ext
        print new_file
        print emoji['src']
        gfs_fileuploader(new_file, 'image/' + ext, emoji['src'])
        item = {
                "name": name,
                "aliases": [],
                "extension": ext,
                "_updatedAt": {
                    "$date": ts
                    }
                }
        item = json.dumps(item)
        import pprint
        pprint.pprint(item)
        item = loads(item)
        new_emojis.append(item)
    except Exception as e:
        print "error getting image"
        traceback.print_exc(e)
        traceback.print_tb(e)



emoji_db = db.rocketchat_custom_emoji
result = emoji_db.insert_many(new_emojis)
