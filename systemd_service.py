#!/usr/bin/env python3
"""
Systemd service setup for Deals89 Store scheduler
This script creates and manages a systemd service for running the scheduler continuously
"""

import os
import sys
import subprocess
from pathlib import Path

def get_python_path():
    """Get the current Python executable path"""
    return sys.executable

def get_project_path():
    """Get the current project directory path"""
    return str(Path(__file__).parent.absolute())

def get_current_user():
    """Get the current username"""
    return os.getenv('USER', 'www-data')

def create_systemd_service():
    """Create systemd service file content"""
    python_path = get_python_path()
    project_path = get_project_path()
    user = get_current_user()
    
    service_content = f"""[Unit]
Description=Deals89 Store Scheduler Service
After=network.target
Wants=network.target

[Service]
Type=simple
User={user}
Group={user}
WorkingDirectory={project_path}
Environment=PATH={os.path.dirname(python_path)}
ExecStart={python_path} scheduler.py run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=deals89-scheduler

# Environment variables (optional - can also use .env file)
# Environment=FLASK_ENV=production
# Environment=DATABASE_URL=your_database_url

[Install]
WantedBy=multi-user.target
"""
    
    return service_content

def install_service():
    """Install the systemd service"""
    try:
        service_content = create_systemd_service()
        service_file = '/etc/systemd/system/deals89-scheduler.service'
        
        # Write service file (requires sudo)
        print("Creating systemd service file...")
        print("This requires sudo privileges.")
        
        # Create temporary file
        temp_file = '/tmp/deals89-scheduler.service'
        with open(temp_file, 'w') as f:
            f.write(service_content)
        
        # Copy to systemd directory
        subprocess.run(['sudo', 'cp', temp_file, service_file], check=True)
        subprocess.run(['sudo', 'chmod', '644', service_file], check=True)
        
        # Reload systemd
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        
        # Enable service
        subprocess.run(['sudo', 'systemctl', 'enable', 'deals89-scheduler'], check=True)
        
        print("✅ Systemd service installed successfully!")
        print(f"Service file created at: {service_file}")
        print()
        print("To manage the service:")
        print("  sudo systemctl start deals89-scheduler    # Start the service")
        print("  sudo systemctl stop deals89-scheduler     # Stop the service")
        print("  sudo systemctl restart deals89-scheduler  # Restart the service")
        print("  sudo systemctl status deals89-scheduler   # Check service status")
        print("  sudo journalctl -u deals89-scheduler -f   # View logs")
        
        # Clean up temp file
        os.remove(temp_file)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing service: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def uninstall_service():
    """Uninstall the systemd service"""
    try:
        # Stop and disable service
        subprocess.run(['sudo', 'systemctl', 'stop', 'deals89-scheduler'], 
                      capture_output=True)
        subprocess.run(['sudo', 'systemctl', 'disable', 'deals89-scheduler'], 
                      capture_output=True)
        
        # Remove service file
        service_file = '/etc/systemd/system/deals89-scheduler.service'
        subprocess.run(['sudo', 'rm', '-f', service_file], check=True)
        
        # Reload systemd
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        
        print("✅ Systemd service uninstalled successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error uninstalling service: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def show_service_status():
    """Show the current service status"""
    try:
        result = subprocess.run(['systemctl', 'status', 'deals89-scheduler'], 
                               capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"❌ Error checking service status: {e}")

def show_logs():
    """Show service logs"""
    try:
        subprocess.run(['sudo', 'journalctl', '-u', 'deals89-scheduler', '-n', '50'])
    except Exception as e:
        print(f"❌ Error showing logs: {e}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python systemd_service.py [install|uninstall|status|logs|start|stop|restart]")
        print()
        print("Commands:")
        print("  install   - Install the systemd service")
        print("  uninstall - Remove the systemd service")
        print("  status    - Show service status")
        print("  logs      - Show service logs")
        print("  start     - Start the service")
        print("  stop      - Stop the service")
        print("  restart   - Restart the service")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'install':
        print("Installing Deals89 Scheduler as systemd service...")
        print(f"Python path: {get_python_path()}")
        print(f"Project path: {get_project_path()}")
        print(f"User: {get_current_user()}")
        print()
        install_service()
        
    elif command == 'uninstall':
        print("Uninstalling Deals89 Scheduler service...")
        uninstall_service()
        
    elif command == 'status':
        show_service_status()
        
    elif command == 'logs':
        show_logs()
        
    elif command in ['start', 'stop', 'restart']:
        try:
            subprocess.run(['sudo', 'systemctl', command, 'deals89-scheduler'], check=True)
            print(f"✅ Service {command}ed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error {command}ing service: {e}")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python systemd_service.py' without arguments to see usage.")

if __name__ == "__main__":
    main()