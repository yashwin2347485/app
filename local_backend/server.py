from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import socketio
import random
import string
import uvicorn
import json
import os

# Data file paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
LOCATIONS_FILE = os.path.join(DATA_DIR, "locations.json")
GEOFENCES_FILE = os.path.join(DATA_DIR, "geofences.json")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Load data from files or create empty storage
def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# Load existing data
users_db = load_data(USERS_FILE)
locations_data = load_data(LOCATIONS_FILE)
locations_db = locations_data.get('locations', [])
geofences_data = load_data(GEOFENCES_FILE)
geofences_db = geofences_data.get('geofences', [])

print(f"📂 Loaded {len(users_db)} users, {len(locations_db)} locations")

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

# Create FastAPI app
app = FastAPI()

# Create Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, app)

# ============= Models =============

class UserCreate(BaseModel):
    name: str
    deviceId: str

class User(BaseModel):
    id: str
    name: str
    deviceId: str
    inviteCode: str
    sharedWith: List[str] = []
    createdAt: str
    isLost: bool = False

class LocationUpdate(BaseModel):
    userId: str
    lat: float
    lng: float
    accuracy: Optional[float] = None
    battery: Optional[int] = None

class Location(BaseModel):
    id: str
    userId: str
    lat: float
    lng: float
    timestamp: str
    accuracy: Optional[float] = None
    battery: Optional[int] = None

class InvitationAccept(BaseModel):
    userId: str
    inviteCode: str

class GeofenceCreate(BaseModel):
    userId: str
    name: str
    lat: float
    lng: float
    radius: float
    alertType: str

# ============= User Routes =============

@app.post("/api/users")
async def create_user(input: UserCreate):
    # Check if user already exists
    for user in users_db.values():
        if user['deviceId'] == input.deviceId:
            return user
    
    user = {
        'id': str(uuid.uuid4()),
        'name': input.name,
        'deviceId': input.deviceId,
        'inviteCode': ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
        'sharedWith': [],
        'createdAt': datetime.utcnow().isoformat(),
        'isLost': False
    }
    users_db[user['id']] = user
    save_data(USERS_FILE, users_db)  # Save to file
    return user

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.get("/api/users/device/{device_id}")
async def get_user_by_device(device_id: str):
    for user in users_db.values():
        if user['deviceId'] == device_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/users/accept-invitation")
async def accept_invitation(input: InvitationAccept):
    # Find user with invite code
    target_user = None
    for user in users_db.values():
        if user['inviteCode'] == input.inviteCode:
            target_user = user
            break
    
    if not target_user:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    # Add to sharedWith lists (bidirectional)
    if input.userId in users_db:
        current_user = users_db[input.userId]
        if target_user['id'] not in current_user['sharedWith']:
            current_user['sharedWith'].append(target_user['id'])
        if input.userId not in target_user['sharedWith']:
            target_user['sharedWith'].append(input.userId)
        save_data(USERS_FILE, users_db)  # Save to file
    
    return {"message": "Invitation accepted", "user": target_user}

@app.get("/api/users/{user_id}/shared")
async def get_shared_users(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    shared_users = []
    for shared_id in user['sharedWith']:
        if shared_id in users_db:
            shared_users.append(users_db[shared_id])
    
    return shared_users

# ============= Location Routes =============

@app.post("/api/locations")
async def create_location(input: LocationUpdate):
    location = {
        'id': str(uuid.uuid4()),
        'userId': input.userId,
        'lat': input.lat,
        'lng': input.lng,
        'timestamp': datetime.utcnow().isoformat(),
        'accuracy': input.accuracy,
        'battery': input.battery
    }
    locations_db.append(location)
    
    # Keep only last 1000 locations
    if len(locations_db) > 1000:
        locations_db.pop(0)
    
    # Save to file
    save_data(LOCATIONS_FILE, {'locations': locations_db})
    
    # Emit real-time update
    await sio.emit('location_update', location, room=input.userId)
    
    return location

@app.get("/api/locations/{user_id}/latest")
async def get_latest_location(user_id: str):
    user_locations = [loc for loc in locations_db if loc['userId'] == user_id]
    if not user_locations:
        return None
    return user_locations[-1]

@app.get("/api/locations/{user_id}/history")
async def get_location_history(user_id: str, date: Optional[str] = None):
    user_locations = [loc for loc in locations_db if loc['userId'] == user_id]
    # Return last 100 locations
    return user_locations[-100:]

# ============= Geofence Routes =============

@app.post("/api/geofences")
async def create_geofence(input: GeofenceCreate):
    geofence = {
        'id': str(uuid.uuid4()),
        'userId': input.userId,
        'name': input.name,
        'lat': input.lat,
        'lng': input.lng,
        'radius': input.radius,
        'alertType': input.alertType,
        'createdAt': datetime.utcnow().isoformat(),
        'isActive': True
    }
    geofences_db.append(geofence)
    save_data(GEOFENCES_FILE, {'geofences': geofences_db})
    return geofence

@app.get("/api/geofences/{user_id}")
async def get_geofences(user_id: str):
    return [g for g in geofences_db if g['userId'] == user_id and g['isActive']]

# ============= Socket.IO Events =============

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    user_id = data.get('userId')
    if user_id:
        sio.enter_room(sid, user_id)
        print(f"Client {sid} joined room {user_id}")

# ============= CORS =============

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Main =============

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🗺️  Find My - Backend Server                         ║
║                                                          ║
║   Server starting on:                                    ║
║   👉 http://localhost:8001/api                          ║
║                                                          ║
║   Features:                                              ║
║   ✅ Real-time location tracking                        ║
║   ✅ User management                                     ║
║   ✅ Location sharing                                    ║
║   ✅ WebSocket support                                   ║
║                                                          ║
║   Database: In-memory (no MongoDB needed!)              ║
║                                                          ║
║   Press Ctrl+C to stop the server                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(socket_app, host="0.0.0.0", port=8001, log_level="info")
