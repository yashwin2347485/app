# Find My - Location Tracker

## 🚀 Quick Setup Guide (5 Minutes)

### Prerequisites
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Edge)

### Step 1: Download the Project

Download all files from this repository to a folder on your computer, for example: `C:\Projects\location-tracker`

### Step 2: Install Python Dependencies

Open Command Prompt (Windows) or Terminal (Mac/Linux) and navigate to the backend folder:

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Start the Backend Server

In the backend folder, run:

```bash
python server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Keep this terminal window open!**

### Step 4: Start the Web Server

Open a **NEW** terminal window and navigate to the web folder:

```bash
cd web
python server.py
```

You should see:
```
🗺️  Find My - Location Tracker Web App
Server running on: http://localhost:5000
```

### Step 5: Open in Browser

Open your web browser and go to: **http://localhost:5000**

---

## 🎮 How to Demonstrate

### Simple Demo (1 person):
1. Enter your name
2. Click city buttons to simulate location
3. Show the map updating

### Advanced Demo (Multiple users):
1. **First Tab**: Create user "Student A"
2. Copy the invite code
3. Click a city (e.g., "New York")
4. **Second Tab** (Incognito mode): Create user "Student B"  
5. Enter Student A's invite code
6. Click different city (e.g., "London")
7. **Show both tabs** - locations update in real-time!

---

## 🔧 Troubleshooting

### Problem: "pip is not recognized"
**Solution**: Install Python from python.org and check "Add Python to PATH"

### Problem: Port already in use
**Solution**: 
```bash
# Find and kill process on port 8001 (backend)
netstat -ano | findstr :8001
taskkill /PID <PID_NUMBER> /F

# Find and kill process on port 5000 (web)
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

### Problem: "ModuleNotFoundError"
**Solution**: Make sure you ran `pip install -r requirements.txt` in the backend folder

---

## 📁 Project Structure

```
location-tracker/
├── backend/              # Python FastAPI server
│   ├── server.py        # Main backend code
│   └── requirements.txt # Python dependencies
└── web/                 # Web application
    ├── index.html       # Main web page
    ├── app.js          # JavaScript code
    └── server.py       # Simple HTTP server
```

---

## 💡 Key Features to Highlight

✅ Real-time location tracking
✅ WebSocket for instant updates
✅ Secure invite code system
✅ Interactive map with Leaflet
✅ Multiple device support
✅ Clean, modern UI

---

## 🎓 Technical Stack

- **Backend**: Python, FastAPI, Socket.IO
- **Frontend**: HTML5, CSS3, JavaScript
- **Map**: Leaflet.js (OpenStreetMap)
- **Real-time**: WebSocket protocol
- **Database**: In-memory (no setup needed!)

---

## ⚠️ Important Notes

- For the demo, the database is **in-memory** (data clears on restart)
- Location is **simulated** using city buttons
- Works on localhost only (not internet accessible)
- Perfect for project demonstration!

---

Made by [Your Name] | Course Project 2024
