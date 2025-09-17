from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['your_db']

# Update crops collection
for crop in db.crops.find({'seller_name': {'$exists': True}}):
    db.crops.update_one({'_id': crop['_id']}, {'$set': {'seller_username': crop['seller_name']}})

# Update notifications collection
for note in db.notifications.find({'seller_name': {'$exists': True}}):
    db.notifications.update_one({'_id': note['_id']}, {'$set': {'seller_username': note['seller_name']}})

print("Updated all old records: seller_username now matches seller_name.") 