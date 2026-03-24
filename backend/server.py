from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import socketio
import random
import string

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Create the main app
app = FastAPI()

# Create Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, app)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============= Models =============

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    deviceId: str
    inviteCode: str = Field(default_factory=lambda: ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    sharedWith: List[str] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    isLost: bool = False

class UserCreate(BaseModel):
    name: str
    deviceId: str

class Location(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userId: str
    lat: float
    lng: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    accuracy: Optional[float] = None
    battery: Optional[int] = None

class LocationUpdate(BaseModel):
    userId: str
    lat: float
    lng: float
    accuracy: Optional[float] = None
    battery: Optional[int] = None

class Geofence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userId: str
    name: str
    lat: float
    lng: float
    radius: float  # in meters
    alertType: str  # "enter", "exit", "both"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    isActive: bool = True

class GeofenceCreate(BaseModel):
    userId: str
    name: str
    lat: float
    lng: float
    radius: float
    alertType: str

class InvitationAccept(BaseModel):
    userId: str
    inviteCode: str

class LostDeviceRequest(BaseModel):
    userId: str
    isLost: bool

# ============= User Routes =============

@api_router.post("/users", response_model=User)
async def create_user(input: UserCreate):
    # Check if user already exists with this deviceId
    existing_user = await db.users.find_one({"deviceId": input.deviceId})
    if existing_user:
        return User(**existing_user)
    
    user = User(**input.dict())
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.get("/users/device/{device_id}", response_model=User)
async def get_user_by_device(device_id: str):
    user = await db.users.find_one({"deviceId": device_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.post("/users/accept-invitation")
async def accept_invitation(input: InvitationAccept):
    # Find the user with the invite code
    target_user = await db.users.find_one({"inviteCode": input.inviteCode})
    if not target_user:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    # Add target user to current user's sharedWith list
    current_user = await db.users.find_one({"id": input.userId})
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user["id"] not in current_user.get("sharedWith", []):
        await db.users.update_one(
            {"id": input.userId},
            {"$addToSet": {"sharedWith": target_user["id"]}}
        )
    
    # Add current user to target user's sharedWith list (bidirectional)
    if input.userId not in target_user.get("sharedWith", []):
        await db.users.update_one(
            {"id": target_user["id"]},
            {"$addToSet": {"sharedWith": input.userId}}
        )
    
    return {"message": "Invitation accepted", "user": User(**target_user)}

@api_router.get("/users/{user_id}/shared", response_model=List[User])
async def get_shared_users(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    shared_users = []
    for shared_id in user.get("sharedWith", []):
        shared_user = await db.users.find_one({"id": shared_id})
        if shared_user:
            shared_users.append(User(**shared_user))
    
    return shared_users

@api_router.post("/users/lost-device")
async def set_lost_device(input: LostDeviceRequest):
    result = await db.users.update_one(
        {"id": input.userId},
        {"$set": {"isLost": input.isLost}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Emit socket event to notify the lost device
    await sio.emit('device_lost_status', {
        'userId': input.userId,
        'isLost': input.isLost
    }, room=input.userId)
    
    return {"message": "Lost device status updated"}

# ============= Location Routes =============

@api_router.post("/locations", response_model=Location)
async def create_location(input: LocationUpdate):
    location = Location(**input.dict())
    await db.locations.insert_one(location.dict())
    
    # Emit real-time update via Socket.IO
    await sio.emit('location_update', location.dict(), room=input.userId)
    
    # Check geofences
    await check_geofences(input.userId, input.lat, input.lng)
    
    return location

@api_router.get("/locations/{user_id}/latest", response_model=Optional[Location])
async def get_latest_location(user_id: str):
    location = await db.locations.find_one(
        {"userId": user_id},
        sort=[("timestamp", -1)]
    )
    if not location:
        return None
    return Location(**location)

@api_router.get("/locations/{user_id}/history")
async def get_location_history(user_id: str, date: Optional[str] = None):
    query = {"userId": user_id}
    
    if date:
        # Parse date and get locations for that day
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        query["timestamp"] = {"$gte": start_of_day, "$lt": end_of_day}
    else:
        # Get last 24 hours
        query["timestamp"] = {"$gte": datetime.utcnow() - timedelta(days=1)}
    
    locations = await db.locations.find(query).sort("timestamp", -1).to_list(1000)
    return [Location(**loc).dict() for loc in locations]

# ============= Geofence Routes =============

@api_router.post("/geofences", response_model=Geofence)
async def create_geofence(input: GeofenceCreate):
    geofence = Geofence(**input.dict())
    await db.geofences.insert_one(geofence.dict())
    return geofence

@api_router.get("/geofences/{user_id}", response_model=List[Geofence])
async def get_geofences(user_id: str):
    geofences = await db.geofences.find({"userId": user_id, "isActive": True}).to_list(100)
    return [Geofence(**geo) for geo in geofences]

@api_router.delete("/geofences/{geofence_id}")
async def delete_geofence(geofence_id: str):
    result = await db.geofences.update_one(
        {"id": geofence_id},
        {"$set": {"isActive": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Geofence not found")
    return {"message": "Geofence deleted"}

# ============= Helper Functions =============

async def check_geofences(user_id: str, lat: float, lng: float):
    """Check if user entered/exited any geofences"""
    geofences = await db.geofences.find({"userId": user_id, "isActive": True}).to_list(100)
    
    for geofence_data in geofences:
        geofence = Geofence(**geofence_data)
        distance = calculate_distance(lat, lng, geofence.lat, geofence.lng)
        
        if distance <= geofence.radius:
            # User is inside geofence
            if geofence.alertType in ["enter", "both"]:
                await sio.emit('geofence_alert', {
                    'type': 'enter',
                    'geofenceName': geofence.name,
                    'userId': user_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=user_id)

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates in meters using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    return distance

# ============= Socket.IO Events =============

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    """Join a room for real-time updates"""
    user_id = data.get('userId')
    if user_id:
        sio.enter_room(sid, user_id)
        logger.info(f"Client {sid} joined room {user_id}")

@sio.event
async def leave_room(sid, data):
    """Leave a room"""
    user_id = data.get('userId')
    if user_id:
        sio.leave_room(sid, user_id)
        logger.info(f"Client {sid} left room {user_id}")

@sio.event
async def location_update_realtime(sid, data):
    """Handle real-time location updates via Socket.IO"""
    try:
        location = Location(**data)
        await db.locations.insert_one(location.dict())
        
        # Broadcast to all clients in the user's room
        await sio.emit('location_update', location.dict(), room=data['userId'])
        
        # Check geofences
        await check_geofences(data['userId'], data['lat'], data['lng'])
        
    except Exception as e:
        logger.error(f"Error handling location update: {e}")

# ============= Include Router =============

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
