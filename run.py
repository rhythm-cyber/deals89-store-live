#!/usr/bin/env python3
"""
Development server runner for the affiliate deal aggregator.
"""

from app import app
import os

if __name__ == '__main__':
    # Get debug mode from environment
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Get port from environment
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting Flask development server on port {port}")
    print(f"Debug mode: {debug_mode}")
    print("Access the application at: http://localhost:5000")
    print("Admin panel at: http://localhost:5000/admin/login")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )