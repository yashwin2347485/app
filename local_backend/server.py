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
from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'location_tracker')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

print(f"📂 Connected to MongoDB: {DB_NAME}")

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

class LocationUpdate(BaseModel):
    userId: str
    lat: float
    lng: float
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

class NotificationCreate(BaseModel):
    userId: str
    message: str
    type: str  # 'location_change', 'geofence', 'alert'

# ============= User Routes =============

@app.post("/api/users")
async def create_user(input: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"deviceId": input.deviceId})
    if existing_user:
        existing_user['_id'] = str(existing_user['_id'])
        return existing_user
    
    user = {
        'id': str(uuid.uuid4()),
        'name': input.name,
        'deviceId': input.deviceId,
        'inviteCode': ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
        'sharedWith': [],
        'createdAt': datetime.utcnow().isoformat(),
        'isLost': False
    }
    
    await db.users.insert_one(user)
    return user

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user['_id'] = str(user['_id'])
    return user

@app.get("/api/users/device/{device_id}")
async def get_user_by_device(device_id: str):
    user = await db.users.find_one({"deviceId": device_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user['_id'] = str(user['_id'])
    return user

@app.post("/api/users/accept-invitation")
async def accept_invitation(input: InvitationAccept):
    # Find user with invite code
    target_user = await db.users.find_one({"inviteCode": input.inviteCode})
    if not target_user:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    # Add to sharedWith lists (bidirectional)
    current_user = await db.users.find_one({"id": input.userId})
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update current user's sharedWith
    if target_user['id'] not in current_user.get('sharedWith', []):
        await db.users.update_one(
            {"id": input.userId},
            {"$addToSet": {"sharedWith": target_user['id']}}
        )
    
    # Update target user's sharedWith (bidirectional)
    if input.userId not in target_user.get('sharedWith', []):
        await db.users.update_one(
            {"id": target_user['id']},
            {"$addToSet": {"sharedWith": input.userId}}
        )
    
    target_user['_id'] = str(target_user['_id'])
    return {"message": "Invitation accepted", "user": target_user}

@app.get("/api/users/{user_id}/shared")
async def get_shared_users(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    shared_users = []
    for shared_id in user.get('sharedWith', []):
        shared_user = await db.users.find_one({"id": shared_id})
        if shared_user:
            shared_user['_id'] = str(shared_user['_id'])
            shared_users.append(shared_user)
    
    return shared_users

@app.post("/api/users/lost-device")
async def set_lost_device(userId: str, isLost: bool):
    result = await db.users.update_one(
        {"id": userId},
        {"$set": {"isLost": isLost}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Emit socket event
    await sio.emit('device_lost_status', {
        'userId': userId,
        'isLost': isLost
    }, room=userId)
    
    return {"message": "Lost device status updated"}

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
    
    await db.locations.insert_one(location)
    
    # Get user info for notification
    user = await db.users.find_one({"id": input.userId})
    
    # Emit real-time update to user's room
    await sio.emit('location_update', location, room=input.userId)
    
    # Send notification to all friends
    if user:
        for friend_id in user.get('sharedWith', []):
            notification = {
                'id': str(uuid.uuid4()),
                'userId': friend_id,
                'fromUser': user['name'],
                'fromUserId': input.userId,
                'message': f"{user['name']} moved to a new location",
                'type': 'location_change',
                'lat': input.lat,
                'lng': input.lng,
                'timestamp': datetime.utcnow().isoformat(),
                'read': False
            }
            await db.notifications.insert_one(notification)
            
            # Emit notification via socket
            await sio.emit('notification', notification, room=friend_id)
    
    return location

@app.get("/api/locations/{user_id}/latest")
async def get_latest_location(user_id: str):
    location = await db.locations.find_one(
        {"userId": user_id},
        sort=[("timestamp", -1)]
    )
    if not location:
        return None
    location['_id'] = str(location['_id'])
    return location

@app.get("/api/locations/{user_id}/history")
async def get_location_history(user_id: str, date: Optional[str] = None):
    query = {"userId": user_id}
    
    if date:
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        query["timestamp"] = {"$gte": start_of_day.isoformat(), "$lt": end_of_day.isoformat()}
    else:
        # Get last 24 hours
        query["timestamp"] = {"$gte": (datetime.utcnow() - timedelta(days=1)).isoformat()}
    
    locations = await db.locations.find(query).sort("timestamp", -1).limit(100).to_list(100)
    for loc in locations:
        loc['_id'] = str(loc['_id'])
    return locations

# ============= Notification Routes =============

@app.get("/api/notifications/{user_id}")
async def get_notifications(user_id: str, unread_only: bool = False):
    query = {"userId": user_id}
    if unread_only:
        query["read"] = False
    
    notifications = await db.notifications.find(query).sort("timestamp", -1).limit(50).to_list(50)
    for notif in notifications:
        notif['_id'] = str(notif['_id'])
    return notifications

@app.post("/api/notifications/{notification_id}/mark-read")
async def mark_notification_read(notification_id: str):
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

@app.delete("/api/notifications/{user_id}/clear")
async def clear_notifications(user_id: str):
    await db.notifications.delete_many({"userId": user_id})
    return {"message": "Notifications cleared"}

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
    await db.geofences.insert_one(geofence)
    return geofence

@app.get("/api/geofences/{user_id}")
async def get_geofences(user_id: str):
    geofences = await db.geofences.find({"userId": user_id, "isActive": True}).to_list(100)
    for geo in geofences:
        geo['_id'] = str(geo['_id'])
    return geofences

@app.delete("/api/geofences/{geofence_id}")
async def delete_geofence(geofence_id: str):
    result = await db.geofences.update_one(
        {"id": geofence_id},
        {"$set": {"isActive": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Geofence not found")
    return {"message": "Geofence deleted"}

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

@sio.event
async def leave_room(sid, data):
    user_id = data.get('userId')
    if user_id:
        sio.leave_room(sid, user_id)
        print(f"Client {sid} left room {user_id}")

# ============= CORS =============

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Startup Event =============

@app.on_event("startup")
async def startup_event():
    # Create indexes for better performance
    await db.users.create_index("id", unique=True)
    await db.users.create_index("deviceId", unique=True)
    await db.users.create_index("inviteCode", unique=True)
    await db.locations.create_index([("userId", 1), ("timestamp", -1)])
    await db.notifications.create_index([("userId", 1), ("timestamp", -1)])
    print("✅ Database indexes created")

@app.on_event("shutdown")
async def shutdown_event():
    client.close()

# ============= Main =============

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🗺️  Find My - Backend Server with MongoDB            ║
║                                                          ║
║   Server starting on:                                    ║
║   👉 http://localhost:8001/api                          ║
║                                                          ║
║   Features:                                              ║
║   ✅ MongoDB Real-time Database                         ║
║   ✅ Location tracking & history                        ║
║   ✅ User management & sharing                          ║
║   ✅ Real-time notifications                            ║
║   ✅ WebSocket support                                   ║
║                                                          ║
║   Press Ctrl+C to stop the server                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(socket_app, host="0.0.0.0", port=8001, log_level="info")
