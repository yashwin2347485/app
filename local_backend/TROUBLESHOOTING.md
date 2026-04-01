# 🔧 Complete Troubleshooting & Testing Guide

## Step 1: Test MongoDB Connection

### Open Command Prompt and test:
```bash
mongosh
```

If it connects, you'll see:
```
Connecting to: mongodb://127.0.0.1:27017
```

Type `show dbs` to see databases, then `exit` to quit.

If it **doesn't connect**, MongoDB is not running:
```bash
net start MongoDB
```

---

## Step 2: Test Backend API Directly

### Start your backend:
```bash
cd location-tracker
python server.py
```

### In another Command Prompt, test the API:

**Test 1: Create a user**
```bash
curl -X POST http://localhost:8001/api/users -H "Content-Type: application/json" -d "{\"name\":\"Test User\",\"deviceId\":\"test123\"}"
```

**Expected Response:**
```json
{
  "id": "some-uuid-here",
  "name": "Test User",
  "deviceId": "test123",
  "inviteCode": "ABC123",
  "sharedWith": [],
  "createdAt": "2024-...",
  "isLost": false
}
```

**Test 2: Create a location** (use the user ID from above)
```bash
curl -X POST http://localhost:8001/api/locations -H "Content-Type: application/json" -d "{\"userId\":\"PUT-USER-ID-HERE\",\"lat\":40.7128,\"lng\":-74.0060}"
```

**Expected Response:**
```json
{
  "id": "location-uuid",
  "userId": "your-user-id",
  "lat": 40.7128,
  "lng": -74.006,
  "timestamp": "2024-...",
  "accuracy": null,
  "battery": null
}
```

---

## Step 3: Check MongoDB for Data

### Open MongoDB Compass:
1. Connect to: `mongodb://localhost:27017`
2. Look for database: `findmy_location_app` (NEW NAME!)
3. Click on it
4. You should see collections: `users`, `locations`, `notifications`
5. Click `users` → Should see your test user
6. Click `locations` → Should see your test location

---

## Step 4: Frontend Connection Test

### Update app.js if needed:

Make sure API_URL in `/app/local_backend/app.js` is:
```javascript
const API_URL = 'http://localhost:8001/api';
```

### Start web server:
```bash
cd location-tracker
python web_server.py
```

### Open browser console (F12):
1. Go to http://localhost:5000
2. Open Developer Tools (F12)
3. Go to "Console" tab
4. Look for errors

---

## Common Errors & Solutions

### Error: "Failed to setup account"

**Cause:** Backend not running or MongoDB not connected

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8001/api/

# If not running, start it
python server.py

# Check backend terminal for MongoDB connection message
```

### Error: "CORS policy"

**Cause:** CORS not configured properly

**Solution:** Backend already has CORS enabled. If still seeing error:
```python
# In server.py, CORS is already set to allow_origins=["*"]
# Make sure it's there
```

### Error: "User created but no location"

**Cause:** Location API call failing

**Solution:**
1. Check browser console (F12) for errors
2. Check backend terminal for location creation logs
3. Try clicking a city button again
4. Look for the 📍 log message in backend

### Error: "MongoDB connection refused"

**Cause:** MongoDB not running

**Solution:**
```bash
# Start MongoDB
net start MongoDB

# Check if it's running
sc query MongoDB

# Should show: STATE: 4 RUNNING
```

### Error: "Database name already in use"

**Solution:** We changed it to `findmy_location_app`

If you still want to change it:
1. Edit `server.py` line 16:
   ```python
   DB_NAME = os.environ.get('DB_NAME', 'YOUR_CUSTOM_NAME_HERE')
   ```
2. Restart backend

---

## Debugging Checklist

✅ **MongoDB Running?**
```bash
sc query MongoDB
# Should show: RUNNING
```

✅ **Backend Running?**
```bash
curl http://localhost:8001/api/
# Should NOT give "connection refused"
```

✅ **Web Server Running?**
```bash
curl http://localhost:5000
# Should return HTML
```

✅ **Backend Terminal Messages?**
Look for these messages when you create a user:
```
Creating user: Test User, deviceId: test123
✅ User created successfully: Test User (ID: xxx)
```

When you click a city:
```
📍 Creating location for user xxx: (40.7128, -74.006)
✅ Location saved to database with ID: yyy
```

✅ **Browser Console Clean?**
Press F12 → Console tab → Should NOT see red errors

---

## Test Script (Copy-Paste This)

Save as `test_api.py`:

```python
import requests
import json

API_URL = "http://localhost:8001/api"

print("🧪 Testing Backend API...")

# Test 1: Create user
print("\n1️⃣ Creating user...")
response = requests.post(f"{API_URL}/users", json={
    "name": "Test User",
    "deviceId": "test_device_123"
})
print(f"Status: {response.status_code}")
user = response.json()
print(f"User ID: {user['id']}")
print(f"Invite Code: {user['inviteCode']}")

# Test 2: Create location
print("\n2️⃣ Creating location...")
response = requests.post(f"{API_URL}/locations", json={
    "userId": user['id'],
    "lat": 40.7128,
    "lng": -74.0060,
    "accuracy": 10.0,
    "battery": 85
})
print(f"Status: {response.status_code}")
location = response.json()
print(f"Location ID: {location['id']}")

# Test 3: Get latest location
print("\n3️⃣ Getting latest location...")
response = requests.get(f"{API_URL}/locations/{user['id']}/latest")
print(f"Status: {response.status_code}")
latest = response.json()
print(f"Latest location: ({latest['lat']}, {latest['lng']})")

print("\n✅ All tests passed! Your backend is working perfectly!")
```

Run it:
```bash
pip install requests
python test_api.py
```

---

## Still Not Working?

### Send me these details:

1. **Backend Terminal Output:**
   - Copy everything from when you start `python server.py`
   - Look for the MongoDB connection message
   - Look for error messages in red

2. **Browser Console Errors:**
   - Press F12
   - Go to Console tab
   - Copy any red error messages

3. **MongoDB Compass:**
   - Can you see `findmy_location_app` database?
   - Can you see collections inside it?
   - Are there documents in the collections?

4. **Test API Response:**
   - Run the curl commands above
   - Copy the responses

---

## Quick Reset (If Everything is Broken)

```bash
# 1. Stop everything
# Press Ctrl+C in both terminals

# 2. Clear browser data
# In browser: Ctrl+Shift+Delete → Clear "Cookies and site data"

# 3. Drop MongoDB database
mongosh
use findmy_location_app
db.dropDatabase()
exit

# 4. Restart MongoDB
net stop MongoDB
net start MongoDB

# 5. Restart backend
python server.py

# 6. Restart web server
python web_server.py

# 7. Open browser fresh
# Go to http://localhost:5000
```

---

**Follow these steps systematically and you'll find the problem!** 🔍
