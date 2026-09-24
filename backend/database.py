import os
import firebase_admin
from firebase_admin import credentials, firestore

class MemoryStore:
    def __init__(self):
        self.users = {}

    def collection(self, col_name):
        return MemoryCollection(self, [col_name])

    def batch(self):
        return MemoryBatch(self)

class MemoryCollection:
    def __init__(self, store, path):
        self.store = store
        self.path = path

    def document(self, doc_id):
        return MemoryDocument(self.store, self.path + [doc_id])

    def where(self, field, op, value):
        return MemoryQuery(self.store, self.path, field, op, value)

    def stream(self):
        # Return all documents in this collection path
        data = self._get_dict()
        result = []
        for k, v in data.items():
            if isinstance(v, dict) and "_data" in v:
                result.append(MemoryDocRef(k, v["_data"]))
        return result

    def _get_dict(self):
        curr = self.store.users
        for p in self.path:
            if p not in curr:
                curr[p] = {}
            curr = curr[p]
        return curr

class MemoryQuery:
    def __init__(self, store, path, field, op, value):
        self.store = store
        self.path = path
        self.field = field
        self.op = op
        self.value = value

    def stream(self):
        collection = MemoryCollection(self.store, self.path)
        all_docs = collection.stream()
        filtered = []
        for d in all_docs:
            val = d.to_dict().get(self.field)
            if self.op == "==" and val == self.value:
                filtered.append(d)
        return filtered

class MemoryDocument:
    def __init__(self, store, path):
        self.store = store
        self.path = path

    def collection(self, col_name):
        return MemoryCollection(self.store, self.path + [col_name])

    def get(self):
        curr = self.store.users
        for p in self.path[:-1]:
            if p not in curr:
                return MemoryDocRef(self.path[-1], None, exists=False)
            curr = curr[p]
        doc_id = self.path[-1]
        if doc_id in curr and "_data" in curr[doc_id]:
            return MemoryDocRef(doc_id, curr[doc_id]["_data"], exists=True)
        return MemoryDocRef(doc_id, None, exists=False)

    def set(self, data):
        curr = self.store.users
        for p in self.path[:-1]:
            if p not in curr:
                curr[p] = {}
            curr = curr[p]
        doc_id = self.path[-1]
        curr[doc_id] = {"_data": data}

    def update(self, data):
        curr = self.store.users
        for p in self.path[:-1]:
            if p not in curr:
                curr[p] = {}
            curr = curr[p]
        doc_id = self.path[-1]
        if doc_id in curr and "_data" in curr[doc_id]:
            curr[doc_id]["_data"].update(data)

class MemoryDocRef:
    def __init__(self, doc_id, data, exists=True):
        self.id = doc_id
        self._data = data or {}
        self.exists = exists and (data is not None)

    def to_dict(self):
        return self._data

class MemoryBatch:
    def __init__(self, store):
        self.store = store
        self.ops = []

    def set(self, doc_ref, data):
        self.ops.append(('set', doc_ref, data))

    def update(self, doc_ref, data):
        self.ops.append(('update', doc_ref, data))

    def commit(self):
        for op, doc_ref, data in self.ops:
            if op == 'set':
                doc_ref.set(data)
            elif op == 'update':
                doc_ref.update(data)

_memory_store = MemoryStore()

def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"Notice: Firebase Admin running in local memory fallback mode: {e}")

def get_db():
    if not firebase_admin._apps:
        init_firebase()
    try:
        return firestore.client()
    except Exception:
        return _memory_store
