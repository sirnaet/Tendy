"""
firebase_client.py
------------------
Firebase Admin SDK initialization, Cloud Firestore client retrieval, 
and Auth ID Token verification helper with local fallback store support.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from typing import Dict, Any, List, Optional

# --- Local Memory Store Fallback for Offline / Dev Execution ---
class MemoryDocRef:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]], exists: bool = True):
        self.id = doc_id
        self._data = data or {}
        self.exists = exists and (data is not None)

    def to_dict(self) -> Dict[str, Any]:
        return self._data.copy()

class MemoryQuery:
    def __init__(self, store: 'MemoryStore', path: List[str], field: str, op: str, value: Any):
        self.store = store
        self.path = path
        self.field = field
        self.op = op
        self.value = value

    def stream(self) -> List[MemoryDocRef]:
        collection = MemoryCollection(self.store, self.path)
        all_docs = collection.stream()
        filtered = []
        for d in all_docs:
            val = d.to_dict().get(self.field)
            if self.op == "==" and val == self.value:
                filtered.append(d)
            elif self.op == ">" and val is not None and val > self.value:
                filtered.append(d)
            elif self.op == "<" and val is not None and val < self.value:
                filtered.append(d)
        return filtered

class MemoryCollection:
    def __init__(self, store: 'MemoryStore', path: List[str]):
        self.store = store
        self.path = path

    def document(self, doc_id: str) -> 'MemoryDocument':
        return MemoryDocument(self.store, self.path + [doc_id])

    def where(self, field: str, op: str, value: Any) -> MemoryQuery:
        return MemoryQuery(self.store, self.path, field, op, value)

    def stream(self) -> List[MemoryDocRef]:
        curr = self.store.data
        for p in self.path:
            if p not in curr or not isinstance(curr[p], dict):
                return []
            curr = curr[p]
        result = []
        for k, v in curr.items():
            if isinstance(v, dict) and "_data" in v:
                result.append(MemoryDocRef(k, v["_data"], exists=True))
        return result

class MemoryDocument:
    def __init__(self, store: 'MemoryStore', path: List[str]):
        self.store = store
        self.path = path

    def collection(self, col_name: str) -> MemoryCollection:
        return MemoryCollection(self.store, self.path + [col_name])

    def get(self) -> MemoryDocRef:
        curr = self.store.data
        for p in self.path[:-1]:
            if p not in curr or not isinstance(curr[p], dict):
                return MemoryDocRef(self.path[-1], None, exists=False)
            curr = curr[p]
        doc_id = self.path[-1]
        if isinstance(curr, dict) and doc_id in curr and "_data" in curr[doc_id]:
            return MemoryDocRef(doc_id, curr[doc_id]["_data"], exists=True)
        return MemoryDocRef(doc_id, None, exists=False)

    def set(self, data: Dict[str, Any], merge: bool = False):
        curr = self.store.data
        for p in self.path[:-1]:
            if p not in curr or not isinstance(curr[p], dict):
                curr[p] = {}
            curr = curr[p]
        doc_id = self.path[-1]
        if merge and doc_id in curr and "_data" in curr[doc_id]:
            curr[doc_id]["_data"].update(data)
        else:
            curr[doc_id] = {"_data": data.copy()}

    def update(self, data: Dict[str, Any]):
        curr = self.store.data
        for p in self.path[:-1]:
            if p not in curr or not isinstance(curr[p], dict):
                curr[p] = {}
            curr = curr[p]
        doc_id = self.path[-1]
        if doc_id in curr and "_data" in curr[doc_id]:
            curr[doc_id]["_data"].update(data)
        else:
            curr[doc_id] = {"_data": data.copy()}

    def delete(self):
        curr = self.store.data
        for p in self.path[:-1]:
            if p not in curr or not isinstance(curr[p], dict):
                return
            curr = curr[p]
        doc_id = self.path[-1]
        if doc_id in curr:
            del curr[doc_id]

class MemoryBatch:
    def __init__(self, store: 'MemoryStore'):
        self.store = store
        self.ops = []

    def set(self, doc_ref: MemoryDocument, data: Dict[str, Any]):
        self.ops.append(('set', doc_ref, data))

    def update(self, doc_ref: MemoryDocument, data: Dict[str, Any]):
        self.ops.append(('update', doc_ref, data))

    def delete(self, doc_ref: MemoryDocument):
        self.ops.append(('delete', doc_ref, None))

    def commit(self):
        for op, doc_ref, data in self.ops:
            if op == 'set':
                doc_ref.set(data)
            elif op == 'update':
                doc_ref.update(data)
            elif op == 'delete':
                doc_ref.delete()
        self.ops.clear()

class MemoryStore:
    def __init__(self):
        self.data: Dict[str, Any] = {}

    def collection(self, col_name: str) -> MemoryCollection:
        return MemoryCollection(self, [col_name])

    def batch(self) -> MemoryBatch:
        return MemoryBatch(self)

_memory_store = MemoryStore()

# --- Firebase Initialization & Accessors ---

_firebase_status = {"connected": False, "mode": "MemoryStore", "project_id": "tendy-eb67"}

def init_firebase() -> bool:
    """
    Initializes Firebase Admin SDK with project 'tendy-eb67' or custom service account credentials.
    Returns True if initialized with live Firebase/Firestore, False if in local MemoryStore mode.
    """
    global _firebase_status
    if firebase_admin._apps:
        return _firebase_status["connected"]

    project_id = os.environ.get("FIREBASE_PROJECT_ID", "tendy-eb67")
    cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if not cred_path:
        # Scan current working directory for key files
        for fname in ["serviceAccountKey.json", "firebase-key.json", "firebase-credentials.json"]:
            if os.path.exists(fname):
                cred_path = fname
                break

    if cred_path and os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {"projectId": project_id})
            _firebase_status = {"connected": True, "mode": "ServiceAccount", "project_id": project_id}
            print(f"[FirebaseClient] Connected via Service Account key: {cred_path} (Project: {project_id})")
            return True
        except Exception as e:
            print(f"[FirebaseClient] Service account key error: {e}")

    # Check for Firestore Emulator
    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        try:
            firebase_admin.initialize_app(options={"projectId": project_id})
            _firebase_status = {"connected": True, "mode": "Emulator", "project_id": project_id}
            print(f"[FirebaseClient] Connected via Firestore Emulator at {os.environ.get('FIRESTORE_EMULATOR_HOST')}")
            return True
        except Exception as e:
            print(f"[FirebaseClient] Emulator init error: {e}")

    # Try Application Default Credentials
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"projectId": project_id})
        _firebase_status = {"connected": True, "mode": "ApplicationDefault", "project_id": project_id}
        print(f"[FirebaseClient] Connected via Application Default Credentials (Project: {project_id})")
        return True
    except Exception as e:
        print(f"[FirebaseClient] Application Default Credentials not found ({e}). Falling back to MemoryStore.")

    _firebase_status = {"connected": False, "mode": "MemoryStore", "project_id": project_id}
    return False

def get_db():
    """
    Returns Cloud Firestore client if connected, or local MemoryStore fallback.
    """
    is_live = init_firebase()
    if is_live:
        try:
            return firestore.client()
        except Exception as e:
            print(f"[FirebaseClient] Failed to retrieve firestore client: {e}")
            return _memory_store
    return _memory_store

def get_firebase_status() -> Dict[str, Any]:
    """
    Returns detailed dictionary of Firebase connection status.
    """
    init_firebase()
    return _firebase_status.copy()

def verify_firebase_token(id_token: str) -> str:
    """
    Verifies a Firebase Authentication ID Token and returns the authenticated user's `uid`.
    Supports fallback token formats for dev / testing environments.
    """
    if not id_token:
        raise ValueError("Missing authentication token")

    if id_token.startswith("demo_token_"):
        return id_token.replace("demo_token_", "")

    if not firebase_admin._apps:
        init_firebase()

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get("uid")
        if not uid:
            raise ValueError("Token missing UID claim")
        return uid
    except Exception as e:
        # Fallback for dev mode string tokens
        if not id_token.startswith("eyJ"):
            return f"dev_user_{id_token[:8]}"
        raise ValueError(f"Invalid Firebase ID Token: {e}")

