import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLocation } from '../../contexts/LocationContext';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface HistoryLocation {
  lat: number;
  lng: number;
  timestamp: string;
  accuracy: number | null;
}

export default function HistoryScreen() {
  const { userId } = useLocation();
  const [history, setHistory] = useState<HistoryLocation[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (userId) {
      loadHistory();
    }
  }, [userId]);

  const loadHistory = async () => {
    if (!userId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/locations/${userId}/history`);
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    }
  };

  const groupByDate = (locations: HistoryLocation[]) => {
    const grouped: { [key: string]: HistoryLocation[] } = {};
    locations.forEach((loc) => {
      const date = formatDate(loc.timestamp);
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(loc);
    });
    return grouped;
  };

  const renderHistoryItem = ({ item }: { item: HistoryLocation }) => {
    return (
      <View style={styles.historyItem}>
        <View style={styles.timelineMarker}>
          <View style={styles.timelineDot} />
          <View style={styles.timelineLine} />
        </View>
        <View style={styles.historyContent}>
          <Text style={styles.historyTime}>{formatTime(item.timestamp)}</Text>
          <Text style={styles.historyCoords}>
            {item.lat.toFixed(6)}, {item.lng.toFixed(6)}
          </Text>
          {item.accuracy && (
            <Text style={styles.historyAccuracy}>
              Accuracy: ±{Math.round(item.accuracy)}m
            </Text>
          )}
        </View>
      </View>
    );
  };

  const renderSection = (date: string, locations: HistoryLocation[]) => {
    return (
      <View key={date} style={styles.section}>
        <Text style={styles.sectionTitle}>{date}</Text>
        <FlatList
          data={locations}
          renderItem={renderHistoryItem}
          keyExtractor={(item, index) => `${item.timestamp}-${index}`}
          scrollEnabled={false}
        />
      </View>
    );
  };

  const groupedHistory = groupByDate(history);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Location History</Text>
        <TouchableOpacity onPress={loadHistory} style={styles.refreshButton}>
          <Ionicons name="refresh" size={24} color="#007AFF" />
        </TouchableOpacity>
      </View>

      {history.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="time-outline" size={64} color="#ccc" />
          <Text style={styles.emptyText}>No history available</Text>
          <Text style={styles.emptySubtext}>
            Your location history will appear here
          </Text>
        </View>
      ) : (
        <FlatList
          data={Object.keys(groupedHistory)}
          renderItem={({ item: date }) => renderSection(date, groupedHistory[date])}
          keyExtractor={(item) => item}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#000',
  },
  refreshButton: {
    padding: 8,
  },
  listContent: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 12,
  },
  historyItem: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  timelineMarker: {
    alignItems: 'center',
    marginRight: 16,
  },
  timelineDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#007AFF',
    marginTop: 4,
  },
  timelineLine: {
    width: 2,
    flex: 1,
    backgroundColor: '#E5E5EA',
    marginTop: 4,
  },
  historyContent: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  historyTime: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  historyCoords: {
    fontSize: 14,
    color: '#666',
    fontFamily: 'monospace',
  },
  historyAccuracy: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
  },
});
