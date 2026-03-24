import React, { useEffect, useRef, useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Text, Platform } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { Ionicons } from '@expo/vector-icons';

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

interface MapComponentProps {
  myLocation: LocationData | null;
  sharedLocations: Map<string, UserLocation>;
}

export default function MapComponent({ myLocation, sharedLocations }: MapComponentProps) {
  const mapRef = useRef<MapView>(null);
  const [followUser, setFollowUser] = useState(true);

  useEffect(() => {
    if (myLocation && followUser && mapRef.current) {
      mapRef.current.animateToRegion({
        latitude: myLocation.lat,
        longitude: myLocation.lng,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      });
    }
  }, [myLocation, followUser]);

  const centerOnMyLocation = () => {
    if (myLocation && mapRef.current) {
      setFollowUser(true);
      mapRef.current.animateToRegion({
        latitude: myLocation.lat,
        longitude: myLocation.lng,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      });
    }
  };

  const onMapPanOrZoom = () => {
    setFollowUser(false);
  };

  return (
    <View style={styles.mapContainer}>
      <MapView
        ref={mapRef}
        style={styles.map}
        provider={Platform.OS === 'android' ? PROVIDER_GOOGLE : undefined}
        initialRegion={{
          latitude: myLocation?.lat || 37.78825,
          longitude: myLocation?.lng || -122.4324,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        }}
        showsUserLocation={false}
        showsMyLocationButton={false}
        onPanDrag={onMapPanOrZoom}
        onRegionChangeComplete={onMapPanOrZoom}
      >
        {myLocation && (
          <Marker
            coordinate={{
              latitude: myLocation.lat,
              longitude: myLocation.lng,
            }}
            title="You"
            pinColor="#007AFF"
          >
            <View style={styles.myMarker}>
              <View style={styles.myMarkerInner} />
            </View>
          </Marker>
        )}

        {Array.from(sharedLocations.values()).map((userLoc) => {
          if (!userLoc.location) return null;
          return (
            <Marker
              key={userLoc.userId}
              coordinate={{
                latitude: userLoc.location.lat,
                longitude: userLoc.location.lng,
              }}
              title={userLoc.userName}
            >
              <View style={[styles.sharedMarker, userLoc.isLost && styles.lostMarker]}>
                <Ionicons 
                  name="person" 
                  size={20} 
                  color={userLoc.isLost ? '#FF3B30' : '#fff'} 
                />
              </View>
            </Marker>
          );
        })}
      </MapView>

      <TouchableOpacity
        style={styles.centerButton}
        onPress={centerOnMyLocation}
      >
        <Ionicons name="locate" size={24} color={followUser ? '#007AFF' : '#666'} />
      </TouchableOpacity>

      <View style={styles.infoCard}>
        <Text style={styles.infoText}>
          {myLocation 
            ? `Tracking your location • ${sharedLocations.size} shared`
            : 'Getting your location...'}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  mapContainer: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  myMarker: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#007AFF',
    borderWidth: 4,
    borderColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  myMarkerInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#fff',
  },
  sharedMarker: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  lostMarker: {
    backgroundColor: '#FF3B30',
  },
  centerButton: {
    position: 'absolute',
    right: 16,
    bottom: 100,
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  infoCard: {
    position: 'absolute',
    top: 16,
    left: 16,
    right: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});
