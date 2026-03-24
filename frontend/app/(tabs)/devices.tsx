import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  TextInput,
  Modal,
  Alert,
  Share,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLocation } from '../../contexts/LocationContext';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function DevicesScreen() {
  const { sharedLocations, userId, inviteCode, refreshSharedUsers } = useLocation();
  const [modalVisible, setModalVisible] = useState(false);
  const [inviteCodeInput, setInviteCodeInput] = useState('');

  const handleShareInviteCode = async () => {
    try {
      await Share.share({
        message: `Join me on Find My! Use this code to share locations: ${inviteCode}`,
        title: 'Find My - Share Location',
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const handleAcceptInvite = async () => {
    if (!inviteCodeInput.trim()) {
      Alert.alert('Error', 'Please enter an invite code');
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/users/accept-invitation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          inviteCode: inviteCodeInput.trim().toUpperCase(),
        }),
      });

      if (!response.ok) {
        throw new Error('Invalid invite code');
      }

      await refreshSharedUsers();
      setModalVisible(false);
      setInviteCodeInput('');
      Alert.alert('Success', 'Location sharing enabled!');
    } catch (error) {
      console.error('Error accepting invite:', error);
      Alert.alert('Error', 'Invalid invite code. Please try again.');
    }
  };

  const handleMarkAsLost = async (deviceUserId: string) => {
    Alert.alert(
      'Mark as Lost',
      'Are you sure you want to mark this device as lost?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Mark as Lost',
          style: 'destructive',
          onPress: async () => {
            try {
              await fetch(`${BACKEND_URL}/api/users/lost-device`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  userId: deviceUserId,
                  isLost: true,
                }),
              });
              await refreshSharedUsers();
              Alert.alert('Success', 'Device marked as lost');
            } catch (error) {
              Alert.alert('Error', 'Failed to mark device as lost');
            }
          },
        },
      ]
    );
  };

  const renderDevice = ({ item }: { item: any }) => {
    const userLoc = item[1];
    const lastSeen = userLoc.location
      ? new Date(userLoc.location.timestamp).toLocaleString()
      : 'Never';

    return (
      <View style={styles.deviceCard}>
        <View style={styles.deviceIcon}>
          <Ionicons
            name={userLoc.isLost ? 'alert-circle' : 'person'}
            size={32}
            color={userLoc.isLost ? '#FF3B30' : '#007AFF'}
          />
        </View>
        <View style={styles.deviceInfo}>
          <Text style={styles.deviceName}>{userLoc.userName}</Text>
          <Text style={styles.deviceStatus}>
            {userLoc.location ? 'Active' : 'Offline'} • Last seen: {lastSeen}
          </Text>
          {userLoc.isLost && (
            <Text style={styles.lostBadge}>🚨 LOST DEVICE</Text>
          )}
        </View>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleMarkAsLost(userLoc.userId)}
        >
          <Ionicons name="ellipsis-horizontal" size={24} color="#666" />
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Devices</Text>
      </View>

      <View style={styles.inviteSection}>
        <View style={styles.inviteCard}>
          <Text style={styles.inviteTitle}>Your Invite Code</Text>
          <Text style={styles.inviteCode}>{inviteCode}</Text>
          <TouchableOpacity
            style={styles.shareButton}
            onPress={handleShareInviteCode}
          >
            <Ionicons name="share-outline" size={20} color="#007AFF" />
            <Text style={styles.shareButtonText}>Share Code</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.addDeviceSection}>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setModalVisible(true)}
        >
          <Ionicons name="add-circle" size={24} color="#007AFF" />
          <Text style={styles.addButtonText}>Add Device</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.listContainer}>
        <Text style={styles.sectionTitle}>
          Shared Devices ({sharedLocations.size})
        </Text>
        {sharedLocations.size === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="phone-portrait-outline" size={64} color="#ccc" />
            <Text style={styles.emptyText}>No shared devices yet</Text>
            <Text style={styles.emptySubtext}>
              Share your invite code to start tracking
            </Text>
          </View>
        ) : (
          <FlatList
            data={Array.from(sharedLocations.entries())}
            renderItem={renderDevice}
            keyExtractor={(item) => item[0]}
            contentContainerStyle={styles.listContent}
          />
        )}
      </View>

      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Device</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Ionicons name="close" size={28} color="#666" />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalLabel}>Enter Invite Code</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="ABC123"
              value={inviteCodeInput}
              onChangeText={setInviteCodeInput}
              autoCapitalize="characters"
              autoFocus
            />

            <TouchableOpacity
              style={styles.modalButton}
              onPress={handleAcceptInvite}
            >
              <Text style={styles.modalButtonText}>Add Device</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
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
  inviteSection: {
    padding: 16,
  },
  inviteCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  inviteTitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  inviteCode: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
    letterSpacing: 4,
    marginBottom: 16,
  },
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#E3F2FD',
  },
  shareButtonText: {
    fontSize: 16,
    color: '#007AFF',
    marginLeft: 8,
    fontWeight: '600',
  },
  addDeviceSection: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
  },
  addButtonText: {
    fontSize: 16,
    color: '#007AFF',
    marginLeft: 8,
    fontWeight: '600',
  },
  listContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 12,
  },
  listContent: {
    paddingBottom: 16,
  },
  deviceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  deviceIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
  },
  deviceInfo: {
    flex: 1,
    marginLeft: 16,
  },
  deviceName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  deviceStatus: {
    fontSize: 14,
    color: '#666',
  },
  lostBadge: {
    fontSize: 12,
    color: '#FF3B30',
    fontWeight: '600',
    marginTop: 4,
  },
  actionButton: {
    padding: 8,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
  },
  modalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8,
  },
  modalInput: {
    height: 48,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 16,
    fontSize: 18,
    letterSpacing: 2,
    marginBottom: 24,
  },
  modalButton: {
    height: 48,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
