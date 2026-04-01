# 🗄️ MongoDB Local Setup Guide for Windows

## Complete Step-by-Step Installation

### Step 1: Download MongoDB

1. Go to: **https://www.mongodb.com/try/download/community**
2. Select:
   - **Version**: 7.0.x (Latest)
   - **Platform**: Windows
   - **Package**: MSI
3. Click **Download**

### Step 2: Install MongoDB

1. **Run the downloaded .msi file**
2. Click **Next** through the setup
3. **IMPORTANT**: Choose **"Complete" installation** (not Custom)
4. **Install MongoDB as a Service**:
   - ✅ Check "Install MongoDB as a Service"
   - Service Name: `MongoDB`
   - Run service as: `Network Service user`
5. **Install MongoDB Compass** (GUI tool):
   - ✅ Check "Install MongoDB Compass"
6. Click **Install** and wait (takes 2-3 minutes)
7. Click **Finish**

### Step 3: Verify Installation

Open **Command Prompt** and type:
```bash
mongod --version
```

You should see:
```
db version v7.0.x
```

### Step 4: Start MongoDB Service

MongoDB should start automatically. To verify:

```bash
net start MongoDB
```

You should see: `The MongoDB Server (MongoDB) service is starting...`

**OR** Open **Services** (press Win+R, type `services.msc`):
- Find "MongoDB Server (MongoDB)"
- Make sure Status is **"Running"**

### Step 5: Test Connection

Open **Command Prompt** and type:
```bash
mongosh
```

You should see:
```
Current Mongosh Log ID: xxxxx
Connecting to: mongodb://127.0.0.1:27017/
Using MongoDB: 7.0.x
```

Type `exit` to quit.

---

## Alternative: Quick Install with Chocolatey

If you have Chocolatey package manager:

```bash
choco install mongodb
choco install mongodb-compass
```

---

## MongoDB Compass (GUI Tool)

### Open MongoDB Compass:
1. Search for "MongoDB Compass" in Start Menu
2. Open it
3. Connection string should be: `mongodb://localhost:27017`
4. Click **Connect**

### You'll see:
- **Databases** → `admin`, `config`, `local`
- After running your app, you'll see **`location_tracker`** database
- Inside it: `users`, `locations`, `notifications` collections

### View Your Data:
1. Click **location_tracker** database
2. Click **users** collection
3. See all your users with their data!
4. Click **locations** to see location history
5. Click **notifications** to see all notifications

---

## Troubleshooting

### Problem: "mongod is not recognized"

**Solution 1**: Add to PATH manually
1. Open **Environment Variables**
2. Edit **Path** variable
3. Add: `C:\Program Files\MongoDB\Server\7.0\bin`
4. Restart Command Prompt

**Solution 2**: Use full path
```bash
"C:\Program Files\MongoDB\Server\7.0\bin\mongod" --version
```

### Problem: Service won't start

```bash
# Stop the service
net stop MongoDB

# Start it again
net start MongoDB
```

### Problem: Port 27017 already in use

```bash
# Find what's using port 27017
netstat -ano | findstr :27017

# Kill that process
taskkill /PID <PID_NUMBER> /F
```

### Problem: Connection refused

1. Make sure MongoDB service is running
2. Check Windows Firewall (allow port 27017)
3. Try connecting to `127.0.0.1:27017` instead of `localhost:27017`

---

## For Your Teacher Demo

### 1. Show MongoDB Compass:
- "Sir, I'm using MongoDB Compass to view the database"
- Show the `location_tracker` database
- Open `users` collection → Show user accounts
- Open `locations` collection → Show location history
- Open `notifications` collection → Show real-time notifications

### 2. Explain:
- "MongoDB is a NoSQL database used by companies like Facebook, eBay"
- "It stores data in JSON-like documents"
- "Perfect for location data because of flexible schema"
- "Has built-in indexing for fast queries"

### 3. Show Real-time:
- Open app in 2 windows
- Move location in one window
- Refresh MongoDB Compass
- Show new location entry instantly appeared!

---

## Quick Commands Reference

```bash
# Start MongoDB
net start MongoDB

# Stop MongoDB
net stop MongoDB

# Check if running
sc query MongoDB

# Connect with shell
mongosh

# View databases
show dbs

# Use your database
use location_tracker

# View collections
show collections

# View all users
db.users.find()

# View all locations
db.locations.find().limit(10)

# Count notifications
db.notifications.countDocuments()

# Clear all data (if needed)
db.users.deleteMany({})
db.locations.deleteMany({})
db.notifications.deleteMany({})
```

---

## After Installation - Running Your App

1. **Make sure MongoDB is running**:
   ```bash
   net start MongoDB
   ```

2. **Install Python dependencies**:
   ```bash
   cd location-tracker
   pip install -r requirements.txt
   ```

3. **Start your backend** (Terminal 1):
   ```bash
   python server.py
   ```
   
   You'll see:
   ```
   📂 Connected to MongoDB: location_tracker
   ✅ Database indexes created
   ```

4. **Start web server** (Terminal 2):
   ```bash
   python web_server.py
   ```

5. **Open browser**: http://localhost:5000

---

## Data Persistence

✅ **All data stays in MongoDB forever**
✅ **Close app, restart computer** - data is still there
✅ **Perfect for demos** - set up once, use anytime
✅ **Can export data** using MongoDB Compass

---

## Uninstall (if needed)

1. Stop the service:
   ```bash
   net stop MongoDB
   ```

2. Uninstall from **Control Panel** → **Programs**
3. Delete folder: `C:\Program Files\MongoDB`
4. Delete data folder: `C:\data\db` (if exists)

---

**You're all set! MongoDB is now ready for your location tracker app!** 🎉
