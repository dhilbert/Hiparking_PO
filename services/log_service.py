from tinydb import TinyDB, Query

db = TinyDB("messages.json")
Msg = Query()

def log_add(text, ts):
    db.insert({"dm_time": ts, "dm_text": text})

def log_all():
    return db.all()

def log_delete(id):
    db.remove(doc_ids=[id])

def log_update(id, text):
    db.update({"dm_text": text}, doc_ids=[id])
