import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { io, Socket } from 'socket.io-client';
import { Alert, Platform } from 'react-native';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface LocationData {
  lat: number;
  lng: number;
  accuracy: number | null;
  battery: number | null;
  timestamp: string;
}

interface UserLocation {
  userId: string;
  userName: string;
  location: LocationData | null;
  isLost: boolean;
}

interface LocationContextType {
  myLocation: LocationData | null;
  sharedLocations: Map<string, UserLocation>;
  userId: string | null;
  userName: string | null;
  inviteCode: string | null;
  socket: Socket | null;
  refreshSharedUsers: () => Promise<void>;
}

const LocationContext = createContext<LocationContextType>({
  myLocation: null,
  sharedLocations: new Map(),
  userId: null,
  userName: null,
  inviteCode: null,
  socket: null,
  refreshSharedUsers: async () => {},
});

export const useLocation = () => useContext(LocationContext);

export const LocationProvider = ({ children }: { children: React.ReactNode }) => {
  const [myLocation, setMyLocation] = useState<LocationData | null>(null);
  const [sharedLocations, setSharedLocations] = useState<Map<string, UserLocation>>(new Map());
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);
  const locationSubscription = useRef<Location.LocationSubscription | null>(null);

  useEffect(() => {
    initializeApp();
    return () => {
      if (locationSubscription.current) {
        locationSubscription.current.remove();
      }
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  const initializeApp = async () => {
    try {
      const storedUserId = await AsyncStorage.getItem('userId');
      const storedUserName = await AsyncStorage.getItem('userName');
      const storedInviteCode = await AsyncStorage.getItem('inviteCode');

      if (storedUserId && storedUserName && storedInviteCode) {
        setUserId(storedUserId);
        setUserName(storedUserName);
        setInviteCode(storedInviteCode);

        initializeSocket(storedUserId);
        await startLocationTracking(storedUserId);
        await refreshSharedUsers(storedUserId);
      }
    } catch (error) {
      console.error('Error initializing app:', error);
    }
  };

  const initializeSocket = (uid: string) => {
    const socketInstance = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
    });

    socketInstance.on('connect', () => {
      console.log('Socket connected');
      socketInstance.emit('join_room', { userId: uid });
    });

    socketInstance.on('location_update', (data: any) => {
      console.log('Received location update:', data);
      if (data.userId !== uid) {
        updateSharedLocation(data.userId, data);
      }
    });

    socketInstance.on('device_lost_status', (data: any) => {
      console.log('Device lost status:', data);
      if (data.userId === uid && data.isLost) {
        Alert.alert(
          'Lost Device Alert',
          'Your device has been marked as lost!',
          [{ text: 'OK' }]
        );
      }
    });

    socketInstance.on('geofence_alert', (data: any) => {
      console.log('Geofence alert:', data);
      Alert.alert(
        'Geofence Alert',
        `${data.type === 'enter' ? 'Entered' : 'Exited'} ${data.geofenceName}`,
        [{ text: 'OK' }]
      );
    });

    setSocket(socketInstance);
  };

  const startLocationTracking = async (uid: string) => {
    try {
      const { status: foregroundStatus } = await Location.requestForegroundPermissionsAsync();
      
      if (foregroundStatus !== 'granted') {
        Alert.alert('Permission Required', 'Location permission is required to use this app.');
        return;
      }

      if (Platform.OS !== 'web') {
        await Location.requestBackgroundPermissionsAsync();
      }

      locationSubscription.current = await Location.watchPositionAsync(
        {
          accuracy: Location.Accuracy.High,
          timeInterval: 5000,
          distanceInterval: 10,
        },
        async (location) => {
          const locationData: LocationData = {
            lat: location.coords.latitude,
            lng: location.coords.longitude,
            accuracy: location.coords.accuracy,
            battery: null,
            timestamp: new Date().toISOString(),
          };

          setMyLocation(locationData);

          try {
            await fetch(`${BACKEND_URL}/api/locations`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ userId: uid, ...locationData }),
            });
          } catch (error) {
            console.error('Error sending location:', error);
          }
        }
      );
    } catch (error) {
      console.error('Error starting location tracking:', error);
    }
  };

  const updateSharedLocation = (uid: string, locationData: any) => {
    setSharedLocations((prev) => {
      const updated = new Map(prev);
      const existing = updated.get(uid);
      if (existing) {
        updated.set(uid, {
          ...existing,
          location: {
            lat: locationData.lat,
            lng: locationData.lng,
            accuracy: locationData.accuracy,
            battery: locationData.battery,
            timestamp: locationData.timestamp,
          },
        });
      }
      return updated;
    });
  };

  const refreshSharedUsers = async (uid?: string) => {
    const targetUserId = uid || userId;
    if (!targetUserId) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${targetUserId}/shared`);
      if (!response.ok) throw new Error('Failed to fetch shared users');

      const sharedUsers = await response.json();
      const newSharedLocations = new Map<string, UserLocation>();

      for (const user of sharedUsers) {
        const locResponse = await fetch(`${BACKEND_URL}/api/locations/${user.id}/latest`);
        const location = locResponse.ok ? await locResponse.json() : null;

        newSharedLocations.set(user.id, {
          userId: user.id,
          userName: user.name,
          location: location ? {
            lat: location.lat,
            lng: location.lng,
            accuracy: location.accuracy,
            battery: location.battery,
            timestamp: location.timestamp,
          } : null,
          isLost: user.isLost || false,
        });
      }

      setSharedLocations(newSharedLocations);
    } catch (error) {
      console.error('Error refreshing shared users:', error);
    }
  };

  return (
    <LocationContext.Provider
      value={{
        myLocation,
        sharedLocations,
        userId,
        userName,
        inviteCode,
        socket,
        refreshSharedUsers,
      }}
    >
      {children}
    </LocationContext.Provider>
  );
};
