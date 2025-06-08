from pymongo import MongoClient
import os

def get_mongo_client():
    # Use environment variable for URI or hardcode for local dev
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    print(uri)
    return MongoClient(uri)

def get_schedule_collection():
    client = get_mongo_client()
    db = client["assistant_db"]
    return db["schedules"]

def save_schedule_to_mongo(day, schedule):
    col = get_schedule_collection()
    col.update_one({"day": day}, {"$set": {"schedule": schedule}}, upsert=True)

def get_schedule_from_mongo(day):
    col = get_schedule_collection()
    doc = col.find_one({"day": day})
    return doc["schedule"] if doc else None