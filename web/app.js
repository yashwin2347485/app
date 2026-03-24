// API Configuration
const API_URL = window.location.origin + '/api';
let socket = null;
let map = null;
let markers = {};
let currentUser = null;
let updateInterval = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    checkExistingUser();
});

// Check if user already exists
function checkExistingUser() {
    const userData = localStorage.getItem('findMyUser');
    if (userData) {
        currentUser = JSON.parse(userData);
        showMainScreen();
        initializeMap();
        connectSocket();
        loadSharedDevices();
    }
}

// Setup new user
async function setupUser() {
    const name = document.getElementById('setupName').value.trim();
    if (!name) {
        alert('Please enter your name');
        return;
    }

    const deviceId = 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    try {
        const response = await fetch(`${API_URL}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, deviceId })
        });

        if (!response.ok) throw new Error('Failed to create user');

        currentUser = await response.json();
        localStorage.setItem('findMyUser', JSON.stringify(currentUser));

        showMainScreen();
        initializeMap();
        connectSocket();
        startLocationUpdates();
    } catch (error) {
        console.error('Setup error:', error);
        alert('Failed to set up account. Please try again.');
    }
}

// Show main screen
function showMainScreen() {
    document.getElementById('setupScreen').classList.add('hidden');
    document.getElementById('mainScreen').classList.remove('hidden');

    document.getElementById('userInfo').innerHTML = `
        <div style="font-weight: 600; font-size: 18px; margin-bottom: 5px;">${currentUser.name}</div>
        <div style="color: #666; font-size: 14px;">User ID: ${currentUser.id.substr(0, 8)}...</div>
    `;
    document.getElementById('inviteCode').textContent = currentUser.inviteCode;
}

// Initialize map
function initializeMap() {
    map = L.map('map').setView([20.5937, 78.9629], 4); // Center on India

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // Add custom marker for current user
    const myIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #007AFF;
            border: 4px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        "></div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    markers[currentUser.id] = L.marker([20.5937, 78.9629], { icon: myIcon })
        .addTo(map)
        .bindPopup(`<b>You (${currentUser.name})</b>`);
}

// Connect to Socket.IO
function connectSocket() {
    socket = io(API_URL.replace('/api', ''));

    socket.on('connect', () => {
        console.log('Socket connected');
        socket.emit('join_room', { userId: currentUser.id });
    });

    socket.on('location_update', (data) => {
        console.log('Received location update:', data);
        if (data.userId !== currentUser.id) {
            updateSharedLocationOnMap(data);
        }
    });

    socket.on('disconnect', () => {
        console.log('Socket disconnected');
    });
}

// Simulate location
async function simulateLocation(lat, lng, cityName) {
    if (!currentUser) return;

    try {
        const response = await fetch(`${API_URL}/locations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: currentUser.id,
                lat: lat,
                lng: lng,
                accuracy: 10,
                battery: 85
            })
        });

        if (!response.ok) throw new Error('Failed to update location');

        // Update map
        if (markers[currentUser.id]) {
            markers[currentUser.id].setLatLng([lat, lng]);
            map.setView([lat, lng], 12);
        }

        document.getElementById('locationStatus').innerHTML = `
            <div class="status status-success">
                📍 Location set to ${cityName}<br>
                Coordinates: ${lat.toFixed(4)}, ${lng.toFixed(4)}
            </div>
        `;
    } catch (error) {
        console.error('Location update error:', error);
        document.getElementById('locationStatus').innerHTML = `
            <div class="status status-error">❌ Failed to update location</div>
        `;
    }
}

// Use real location
function useRealLocation() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
    }

    document.getElementById('locationStatus').innerHTML = `
        <div class="status status-info">📡 Getting your location...</div>
    `;

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            try {
                const response = await fetch(`${API_URL}/locations`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        userId: currentUser.id,
                        lat: lat,
                        lng: lng,
                        accuracy: position.coords.accuracy,
                        battery: null
                    })
                });

                if (!response.ok) throw new Error('Failed to update location');

                // Update map
                if (markers[currentUser.id]) {
                    markers[currentUser.id].setLatLng([lat, lng]);
                    map.setView([lat, lng], 15);
                }

                document.getElementById('locationStatus').innerHTML = `
                    <div class="status status-success">
                        ✅ Real location updated!<br>
                        Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}
                    </div>
                `;
            } catch (error) {
                console.error('Location update error:', error);
                document.getElementById('locationStatus').innerHTML = `
                    <div class="status status-error">❌ Failed to update location</div>
                `;
            }
        },
        (error) => {
            document.getElementById('locationStatus').innerHTML = `
                <div class="status status-error">❌ ${error.message}</div>
            `;
        }
    );
}

// Add friend
async function addFriend() {
    const friendCode = document.getElementById('friendCode').value.trim().toUpperCase();
    if (!friendCode) {
        alert('Please enter an invite code');
        return;
    }

    if (friendCode === currentUser.inviteCode) {
        alert('You cannot add yourself!');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/users/accept-invitation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: currentUser.id,
                inviteCode: friendCode
            })
        });

        if (!response.ok) {
            alert('Invalid invite code. Please check and try again.');
            return;
        }

        const data = await response.json();
        alert(`✅ Successfully added ${data.user.name}!`);
        document.getElementById('friendCode').value = '';
        await loadSharedDevices();
    } catch (error) {
        console.error('Add friend error:', error);
        alert('Failed to add friend. Please try again.');
    }
}

// Load shared devices
async function loadSharedDevices() {
    try {
        const response = await fetch(`${API_URL}/users/${currentUser.id}/shared`);
        if (!response.ok) throw new Error('Failed to load shared devices');

        const sharedUsers = await response.json();
        document.getElementById('deviceCount').textContent = sharedUsers.length;

        const deviceList = document.getElementById('deviceList');
        deviceList.innerHTML = '';

        if (sharedUsers.length === 0) {
            deviceList.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">No shared devices yet</div>';
            return;
        }

        for (const user of sharedUsers) {
            // Fetch latest location
            const locResponse = await fetch(`${API_URL}/locations/${user.id}/latest`);
            const location = locResponse.ok ? await locResponse.json() : null;

            const deviceItem = document.createElement('div');
            deviceItem.className = 'device-item';
            deviceItem.innerHTML = `
                <div>
                    <div class="device-name">${user.name}</div>
                    <div class="device-status">${location ? 'Active' : 'Offline'}</div>
                </div>
                <button class="btn btn-primary" style="width: auto; padding: 8px 16px;" onclick="focusOnDevice('${user.id}')">
                    View
                </button>
            `;
            deviceList.appendChild(deviceItem);

            // Add marker to map
            if (location) {
                addSharedMarker(user, location);
            }
        }
    } catch (error) {
        console.error('Load shared devices error:', error);
    }
}

// Add shared marker to map
function addSharedMarker(user, location) {
    const sharedIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #34C759;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        ">${user.name[0]}</div>`,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });

    if (markers[user.id]) {
        markers[user.id].setLatLng([location.lat, location.lng]);
    } else {
        markers[user.id] = L.marker([location.lat, location.lng], { icon: sharedIcon })
            .addTo(map)
            .bindPopup(`<b>${user.name}</b><br>Last seen: ${new Date(location.timestamp).toLocaleString()}`);
    }
}

// Update shared location on map
function updateSharedLocationOnMap(data) {
    // Find the user in shared devices and update marker
    if (markers[data.userId]) {
        markers[data.userId].setLatLng([data.lat, data.lng]);
        const popup = markers[data.userId].getPopup();
        if (popup) {
            const userName = popup.getContent().match(/<b>(.*?)<\/b>/)[1];
            markers[data.userId].setPopupContent(
                `<b>${userName}</b><br>Last seen: ${new Date(data.timestamp).toLocaleString()}`
            );
        }
    }
}

// Focus on device
function focusOnDevice(userId) {
    if (markers[userId]) {
        const latlng = markers[userId].getLatLng();
        map.setView(latlng, 15);
        markers[userId].openPopup();
    }
}

// Copy invite code
function copyInviteCode() {
    const code = currentUser.inviteCode;
    navigator.clipboard.writeText(code).then(() => {
        alert('✅ Invite code copied: ' + code);
    }).catch(() => {
        alert('Invite code: ' + code);
    });
}

// Start periodic location updates (every 10 seconds)
function startLocationUpdates() {
    if (updateInterval) clearInterval(updateInterval);

    updateInterval = setInterval(() => {
        loadSharedDevices();
    }, 10000);
}
