#!/usr/bin/env python3
"""
Simple HTTP server to serve the Find My web application
Run this script to start the web server on port 5000
"""

import http.server
import socketserver
import os

PORT = 5000
DIRECTORY = "/app/web"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🗺️  Find My - Location Tracker Web App               ║
║                                                          ║
║   Server running on:                                     ║
║   👉 http://localhost:{PORT}                             ║
║                                                          ║
║   Backend API running on:                                ║
║   👉 http://localhost:8001/api                           ║
║                                                          ║
║   Press Ctrl+C to stop the server                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
        """)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped. Goodbye!")
            pass
