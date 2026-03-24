#!/usr/bin/env python3
"""
Backend API Testing for Find My Location Tracking App
Tests all API endpoints according to the review request requirements
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

# Configuration
BASE_URL = "https://find-my-app-217.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class LocationTrackingTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_users = []
        self.test_locations = []
        self.test_geofences = []
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        
        if success:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {message}")
    
    def make_request(self, method: str, endpoint: str, data: dict = None) -> tuple:
        """Make HTTP request and return (success, response, status_code)"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return False, None, 0
            
            return True, response, response.status_code
        except requests.exceptions.RequestException as e:
            return False, str(e), 0
    
    def test_user_creation(self):
        """Test POST /api/users - Create new users"""
        print("\n=== Testing User Management ===")
        
        # Test User 1
        user1_data = {
            "name": "Alice Johnson",
            "deviceId": f"device_alice_{uuid.uuid4().hex[:8]}"
        }
        
        success, response, status_code = self.make_request("POST", "/users", user1_data)
        
        if success and status_code == 200:
            user1 = response.json()
            self.test_users.append(user1)
            
            # Verify user has required fields
            required_fields = ["id", "name", "deviceId", "inviteCode", "sharedWith", "createdAt", "isLost"]
            missing_fields = [field for field in required_fields if field not in user1]
            
            if not missing_fields and len(user1["inviteCode"]) == 6:
                self.log_result("Create User 1", True, f"User created with invite code: {user1['inviteCode']}")
            else:
                self.log_result("Create User 1", False, f"Missing fields: {missing_fields} or invalid invite code")
        else:
            self.log_result("Create User 1", False, f"Status: {status_code}, Response: {response}")
        
        # Test User 2
        user2_data = {
            "name": "Bob Smith",
            "deviceId": f"device_bob_{uuid.uuid4().hex[:8]}"
        }
        
        success, response, status_code = self.make_request("POST", "/users", user2_data)
        
        if success and status_code == 200:
            user2 = response.json()
            self.test_users.append(user2)
            
            # Verify invite codes are unique
            if len(self.test_users) >= 2 and self.test_users[0]["inviteCode"] != user2["inviteCode"]:
                self.log_result("Create User 2", True, f"User created with unique invite code: {user2['inviteCode']}")
            else:
                self.log_result("Create User 2", False, "Invite codes are not unique")
        else:
            self.log_result("Create User 2", False, f"Status: {status_code}, Response: {response}")
    
    def test_user_retrieval(self):
        """Test GET /api/users/{user_id} and GET /api/users/device/{device_id}"""
        if not self.test_users:
            self.log_result("User Retrieval", False, "No test users available")
            return
        
        user = self.test_users[0]
        
        # Test get user by ID
        success, response, status_code = self.make_request("GET", f"/users/{user['id']}")
        
        if success and status_code == 200:
            retrieved_user = response.json()
            if retrieved_user["id"] == user["id"] and retrieved_user["name"] == user["name"]:
                self.log_result("Get User by ID", True)
            else:
                self.log_result("Get User by ID", False, "Retrieved user data doesn't match")
        else:
            self.log_result("Get User by ID", False, f"Status: {status_code}")
        
        # Test get user by device ID
        success, response, status_code = self.make_request("GET", f"/users/device/{user['deviceId']}")
        
        if success and status_code == 200:
            retrieved_user = response.json()
            if retrieved_user["deviceId"] == user["deviceId"]:
                self.log_result("Get User by Device ID", True)
            else:
                self.log_result("Get User by Device ID", False, "Retrieved user data doesn't match")
        else:
            self.log_result("Get User by Device ID", False, f"Status: {status_code}")
    
    def test_invitation_system(self):
        """Test POST /api/users/accept-invitation and bidirectional sharing"""
        if len(self.test_users) < 2:
            self.log_result("Invitation System", False, "Need at least 2 users for invitation testing")
            return
        
        user1, user2 = self.test_users[0], self.test_users[1]
        
        # User1 accepts User2's invite code
        invitation_data = {
            "userId": user1["id"],
            "inviteCode": user2["inviteCode"]
        }
        
        success, response, status_code = self.make_request("POST", "/users/accept-invitation", invitation_data)
        
        if success and status_code == 200:
            result = response.json()
            if "message" in result and "user" in result:
                self.log_result("Accept Invitation", True, "Invitation accepted successfully")
                
                # Test bidirectional sharing - check User1's shared list
                success, response, status_code = self.make_request("GET", f"/users/{user1['id']}/shared")
                
                if success and status_code == 200:
                    shared_users = response.json()
                    user2_in_list = any(u["id"] == user2["id"] for u in shared_users)
                    
                    if user2_in_list:
                        self.log_result("Bidirectional Sharing - User1", True, "User2 found in User1's shared list")
                    else:
                        self.log_result("Bidirectional Sharing - User1", False, "User2 not found in User1's shared list")
                else:
                    self.log_result("Bidirectional Sharing - User1", False, f"Status: {status_code}")
                
                # Check User2's shared list
                success, response, status_code = self.make_request("GET", f"/users/{user2['id']}/shared")
                
                if success and status_code == 200:
                    shared_users = response.json()
                    user1_in_list = any(u["id"] == user1["id"] for u in shared_users)
                    
                    if user1_in_list:
                        self.log_result("Bidirectional Sharing - User2", True, "User1 found in User2's shared list")
                    else:
                        self.log_result("Bidirectional Sharing - User2", False, "User1 not found in User2's shared list")
                else:
                    self.log_result("Bidirectional Sharing - User2", False, f"Status: {status_code}")
            else:
                self.log_result("Accept Invitation", False, "Invalid response format")
        else:
            self.log_result("Accept Invitation", False, f"Status: {status_code}, Response: {response}")
    
    def test_location_tracking(self):
        """Test POST /api/locations and GET /api/locations/{user_id}/latest"""
        print("\n=== Testing Location Tracking ===")
        
        if not self.test_users:
            self.log_result("Location Tracking", False, "No test users available")
            return
        
        user = self.test_users[0]
        
        # Create location update for User1 (San Francisco coordinates)
        location_data = {
            "userId": user["id"],
            "lat": 37.7749,
            "lng": -122.4194,
            "accuracy": 5.0,
            "battery": 85
        }
        
        success, response, status_code = self.make_request("POST", "/locations", location_data)
        
        if success and status_code == 200:
            location = response.json()
            self.test_locations.append(location)
            
            required_fields = ["id", "userId", "lat", "lng", "timestamp"]
            missing_fields = [field for field in required_fields if field not in location]
            
            if not missing_fields:
                self.log_result("Create Location Update", True, f"Location created at ({location['lat']}, {location['lng']})")
            else:
                self.log_result("Create Location Update", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Create Location Update", False, f"Status: {status_code}, Response: {response}")
        
        # Test getting latest location
        success, response, status_code = self.make_request("GET", f"/locations/{user['id']}/latest")
        
        if success and status_code == 200:
            latest_location = response.json()
            if latest_location and latest_location["userId"] == user["id"]:
                self.log_result("Get Latest Location", True, f"Retrieved location: ({latest_location['lat']}, {latest_location['lng']})")
            else:
                self.log_result("Get Latest Location", False, "No location found or invalid data")
        else:
            self.log_result("Get Latest Location", False, f"Status: {status_code}")
        
        # Add second location for User2 if available
        if len(self.test_users) >= 2:
            user2 = self.test_users[1]
            location_data2 = {
                "userId": user2["id"],
                "lat": 40.7128,  # New York coordinates
                "lng": -74.0060,
                "accuracy": 3.0,
                "battery": 92
            }
            
            success, response, status_code = self.make_request("POST", "/locations", location_data2)
            
            if success and status_code == 200:
                self.log_result("Create Location Update - User2", True, "Second user location created")
            else:
                self.log_result("Create Location Update - User2", False, f"Status: {status_code}")
    
    def test_location_history(self):
        """Test GET /api/locations/{user_id}/history"""
        if not self.test_users:
            self.log_result("Location History", False, "No test users available")
            return
        
        user = self.test_users[0]
        
        # Add multiple location updates for history testing
        locations_to_add = [
            {"lat": 37.7849, "lng": -122.4094, "accuracy": 4.0, "battery": 80},
            {"lat": 37.7949, "lng": -122.3994, "accuracy": 6.0, "battery": 75},
            {"lat": 37.8049, "lng": -122.3894, "accuracy": 3.0, "battery": 70}
        ]
        
        for i, loc_data in enumerate(locations_to_add):
            location_data = {
                "userId": user["id"],
                **loc_data
            }
            
            success, response, status_code = self.make_request("POST", "/locations", location_data)
            if success and status_code == 200:
                time.sleep(0.1)  # Small delay to ensure different timestamps
        
        # Test getting location history (last 24 hours)
        success, response, status_code = self.make_request("GET", f"/locations/{user['id']}/history")
        
        if success and status_code == 200:
            history = response.json()
            if isinstance(history, list) and len(history) > 0:
                # Check if sorted by timestamp (most recent first)
                timestamps = [loc["timestamp"] for loc in history]
                is_sorted = all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))
                
                if is_sorted:
                    self.log_result("Location History", True, f"Retrieved {len(history)} location records, properly sorted")
                else:
                    self.log_result("Location History", False, "Location history not sorted by timestamp")
            else:
                self.log_result("Location History", False, "No location history found")
        else:
            self.log_result("Location History", False, f"Status: {status_code}")
    
    def test_geofencing(self):
        """Test geofencing CRUD operations"""
        print("\n=== Testing Geofencing ===")
        
        if not self.test_users:
            self.log_result("Geofencing", False, "No test users available")
            return
        
        user = self.test_users[0]
        
        # Create a geofence around Golden Gate Park
        geofence_data = {
            "userId": user["id"],
            "name": "Golden Gate Park",
            "lat": 37.7694,
            "lng": -122.4862,
            "radius": 500.0,  # 500 meters
            "alertType": "enter"
        }
        
        success, response, status_code = self.make_request("POST", "/geofences", geofence_data)
        
        if success and status_code == 200:
            geofence = response.json()
            self.test_geofences.append(geofence)
            
            required_fields = ["id", "userId", "name", "lat", "lng", "radius", "alertType", "isActive"]
            missing_fields = [field for field in required_fields if field not in geofence]
            
            if not missing_fields and geofence["isActive"]:
                self.log_result("Create Geofence", True, f"Geofence '{geofence['name']}' created with {geofence['radius']}m radius")
            else:
                self.log_result("Create Geofence", False, f"Missing fields: {missing_fields} or inactive geofence")
        else:
            self.log_result("Create Geofence", False, f"Status: {status_code}, Response: {response}")
        
        # Test getting user's geofences
        success, response, status_code = self.make_request("GET", f"/geofences/{user['id']}")
        
        if success and status_code == 200:
            geofences = response.json()
            if isinstance(geofences, list) and len(geofences) > 0:
                active_geofences = [g for g in geofences if g.get("isActive", False)]
                self.log_result("Get User Geofences", True, f"Retrieved {len(active_geofences)} active geofences")
            else:
                self.log_result("Get User Geofences", False, "No geofences found")
        else:
            self.log_result("Get User Geofences", False, f"Status: {status_code}")
        
        # Test geofence entry simulation
        if self.test_geofences:
            geofence = self.test_geofences[0]
            
            # Post location within geofence radius
            location_inside = {
                "userId": user["id"],
                "lat": geofence["lat"] + 0.001,  # Slightly offset but within 500m
                "lng": geofence["lng"] + 0.001,
                "accuracy": 5.0,
                "battery": 88
            }
            
            success, response, status_code = self.make_request("POST", "/locations", location_inside)
            
            if success and status_code == 200:
                self.log_result("Geofence Entry Simulation", True, "Location posted within geofence radius")
            else:
                self.log_result("Geofence Entry Simulation", False, f"Status: {status_code}")
        
        # Test deleting geofence
        if self.test_geofences:
            geofence_id = self.test_geofences[0]["id"]
            
            success, response, status_code = self.make_request("DELETE", f"/geofences/{geofence_id}")
            
            if success and status_code == 200:
                result = response.json()
                if "message" in result:
                    self.log_result("Delete Geofence", True, "Geofence deactivated successfully")
                else:
                    self.log_result("Delete Geofence", False, "Invalid response format")
            else:
                self.log_result("Delete Geofence", False, f"Status: {status_code}")
    
    def test_lost_device(self):
        """Test POST /api/users/lost-device"""
        print("\n=== Testing Lost Device Mode ===")
        
        if not self.test_users:
            self.log_result("Lost Device Mode", False, "No test users available")
            return
        
        user = self.test_users[0]
        
        # Mark device as lost
        lost_device_data = {
            "userId": user["id"],
            "isLost": True
        }
        
        success, response, status_code = self.make_request("POST", "/users/lost-device", lost_device_data)
        
        if success and status_code == 200:
            result = response.json()
            if "message" in result:
                self.log_result("Mark Device as Lost", True, "Device marked as lost successfully")
                
                # Verify the status was updated
                success, response, status_code = self.make_request("GET", f"/users/{user['id']}")
                
                if success and status_code == 200:
                    updated_user = response.json()
                    if updated_user.get("isLost") == True:
                        self.log_result("Verify Lost Status", True, "Lost status confirmed in user record")
                    else:
                        self.log_result("Verify Lost Status", False, "Lost status not updated in user record")
                else:
                    self.log_result("Verify Lost Status", False, f"Status: {status_code}")
            else:
                self.log_result("Mark Device as Lost", False, "Invalid response format")
        else:
            self.log_result("Mark Device as Lost", False, f"Status: {status_code}, Response: {response}")
        
        # Mark device as found
        found_device_data = {
            "userId": user["id"],
            "isLost": False
        }
        
        success, response, status_code = self.make_request("POST", "/users/lost-device", found_device_data)
        
        if success and status_code == 200:
            self.log_result("Mark Device as Found", True, "Device marked as found successfully")
        else:
            self.log_result("Mark Device as Found", False, f"Status: {status_code}")
    
    def test_error_cases(self):
        """Test error handling for invalid requests"""
        print("\n=== Testing Error Cases ===")
        
        # Test invalid user ID
        success, response, status_code = self.make_request("GET", "/users/invalid-user-id")
        
        if success and status_code == 404:
            self.log_result("Invalid User ID Error", True, "Correctly returned 404 for invalid user ID")
        else:
            self.log_result("Invalid User ID Error", False, f"Expected 404, got {status_code}")
        
        # Test invalid invite code
        invalid_invitation = {
            "userId": "invalid-user",
            "inviteCode": "INVALID"
        }
        
        success, response, status_code = self.make_request("POST", "/users/accept-invitation", invalid_invitation)
        
        if success and status_code == 404:
            self.log_result("Invalid Invite Code Error", True, "Correctly returned 404 for invalid invite code")
        else:
            self.log_result("Invalid Invite Code Error", False, f"Expected 404, got {status_code}")
        
        # Test missing required fields
        incomplete_user = {"name": "Incomplete User"}  # Missing deviceId
        
        success, response, status_code = self.make_request("POST", "/users", incomplete_user)
        
        if success and status_code == 422:  # FastAPI validation error
            self.log_result("Missing Required Fields Error", True, "Correctly returned 422 for missing fields")
        else:
            self.log_result("Missing Required Fields Error", False, f"Expected 422, got {status_code}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Find My Location Tracking App Backend Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run test suites in order
        self.test_user_creation()
        self.test_user_retrieval()
        self.test_invitation_system()
        self.test_location_tracking()
        self.test_location_history()
        self.test_geofencing()
        self.test_lost_device()
        self.test_error_cases()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success Rate: {(self.results['passed'] / (self.results['passed'] + self.results['failed']) * 100):.1f}%")
        
        if self.results['errors']:
            print("\n🔍 FAILED TESTS:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        return self.results['failed'] == 0

if __name__ == "__main__":
    tester = LocationTrackingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Backend is working correctly.")
        exit(0)
    else:
        print(f"\n⚠️  {tester.results['failed']} test(s) failed. Please check the issues above.")
        exit(1)