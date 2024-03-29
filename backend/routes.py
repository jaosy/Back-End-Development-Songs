from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health", methods=["GET"])
def health():
    return {"status": "OK"}, 200

@app.route("/count", methods=["GET"])
def count():
    count = db.songs.count_documents({})
    return {"count": count}, 200

@app.route("/song", methods=["GET"])
def songs():
    get_all_songs: list = list(db.songs.find({}))  # Find all songs
    # parse_json needed, else 500 error
    response: tuple = {"songs": parse_json(get_all_songs)}, 200
    return response

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id: int):
    song = db.songs.find_one({"id": id})
    print(song)
    if (song):
        return {"song": parse_json(song)}, 200
    else:
        return {"message": "song with id not found"}, 404

@app.route("/song", methods=["POST"])
def create_song():
    song_data = request.json
    song_id = song_data.get("id")

    if db.songs.find_one({"id": song_id}):
        response = {"message": f"song with id {song_id} already present"}, 302
    else:
        inserted_data: InsertOneResult = db.songs.insert_one(song_data)
        return {"inserted id": parse_json(inserted_data.inserted_id)}, 201

    return response

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id: int):
    song_data = request.json
    set_data = {"$set": song_data}
    if db.songs.find_one({"id": id}):
        result = db.songs.update_one({"id": id}, set_data)

        if result.modified_count == 0:
            response = {"message": "song found, but nothing updated"}, 200

        else:
            response = parse_json(db.songs.find_one({"id": id})), 201
    else:
        return {"message": "song not found"}, 404
    
    return response

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id: int):
    deletion_result = db.songs.delete_one({"id": id})

    if deletion_result.deleted_count == 0:
        response = {"message": "song not found"}, 404

    else:
        response = {}, 204

    return response
