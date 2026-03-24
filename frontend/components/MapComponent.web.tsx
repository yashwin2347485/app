import React from 'react';
import { View, StyleSheet, Text } from 'react-native';
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
  return (
    <View style={styles.webFallback}>
      <Ionicons name="map" size={64} color="#007AFF" />
      <Text style={styles.webFallbackTitle}>Map View</Text>
      <Text style={styles.webFallbackText}>
        Please use the Expo Go app on your mobile device to view the map
      </Text>
      {myLocation && (
        <View style={styles.locationInfo}>
          <Text style={styles.locationText}>Your Location:</Text>
          <Text style={styles.coords}>
            {myLocation.lat.toFixed(6)}, {myLocation.lng.toFixed(6)}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  webFallback: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  webFallbackTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
    marginTop: 16,
    marginBottom: 8,
  },
  webFallbackText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  locationInfo: {
    backgroundColor: '#f5f5f5',
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  locationText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  coords: {
    fontSize: 14,
    color: '#666',
    fontFamily: 'monospace',
  },
});
