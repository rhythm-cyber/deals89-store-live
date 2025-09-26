#!/usr/bin/env python3
"""
Cron job setup and management for Deals89 Store
This script helps set up automated tasks using system cron (Linux/Mac) or Task Scheduler (Windows)
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def get_python_path():
    """Get the current Python executable path"""
    return sys.executable

def get_project_path():
    """Get the current project directory path"""
    return str(Path(__file__).parent.absolute())

def create_cron_jobs_linux():
    """Create cron jobs for Linux/Mac systems"""
    python_path = get_python_path()
    project_path = get_project_path()
    
    cron_jobs = [
        # Daily social media posting at 9:00 AM
        f"0 9 * * * cd {project_path} && {python_path} scheduler.py post >> /var/log/deals89_social.log 2>&1",
        
        # Mark expired deals at 2:00 AM
        f"0 2 * * * cd {project_path} && {python_path} scheduler.py expire >> /var/log/deals89_expire.log 2>&1",
        
        # Cleanup old deals at 3:00 AM
        f"0 3 * * * cd {project_path} && {python_path} scheduler.py cleanup >> /var/log/deals89_cleanup.log 2>&1",
        
        # Health check every 6 hours
        f"0 */6 * * * cd {project_path} && {python_path} scheduler.py health >> /var/log/deals89_health.log 2>&1",
        
        # Backup database daily at 1:00 AM
        f"0 1 * * * cd {project_path} && {python_path} -c \"import shutil; from datetime import datetime; shutil.copy2('instance/deals.db', f'backups/deals_{{datetime.now().strftime(\\'%Y%m%d\\')}.db')\" >> /var/log/deals89_backup.log 2>&1"
    ]
    
    return cron_jobs

def create_windows_tasks():
    """Create Windows Task Scheduler tasks"""
    python_path = get_python_path()
    project_path = get_project_path()
    
    tasks = [
        {
            'name': 'Deals89_SocialPosting',
            'command': f'"{python_path}" scheduler.py post',
            'schedule': 'DAILY',
            'time': '09:00',
            'description': 'Daily social media posting for Deals89'
        },
        {
            'name': 'Deals89_ExpireDeals',
            'command': f'"{python_path}" scheduler.py expire',
            'schedule': 'DAILY',
            'time': '02:00',
            'description': 'Mark expired deals for Deals89'
        },
        {
            'name': 'Deals89_Cleanup',
            'command': f'"{python_path}" scheduler.py cleanup',
            'schedule': 'DAILY',
            'time': '03:00',
            'description': 'Cleanup old deals for Deals89'
        },
        {
            'name': 'Deals89_HealthCheck',
            'command': f'"{python_path}" scheduler.py health',
            'schedule': 'HOURLY',
            'modifier': '6',
            'description': 'Health check for Deals89 every 6 hours'
        }
    ]
    
    return tasks

def setup_linux_cron():
    """Setup cron jobs on Linux/Mac"""
    try:
        # Create log directory
        os.makedirs('/var/log', exist_ok=True)
        
        # Create backup directory
        backup_dir = os.path.join(get_project_path(), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        cron_jobs = create_cron_jobs_linux()
        
        # Get current crontab
        try:
            current_cron = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode()
        except subprocess.CalledProcessError:
            current_cron = ""
        
        # Add new jobs (avoid duplicates)
        new_cron = current_cron
        for job in cron_jobs:
            if job not in current_cron:
                new_cron += f"\n{job}"
        
        # Write new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
        process.communicate(new_cron.encode())
        
        if process.returncode == 0:
            print("✅ Cron jobs setup successfully!")
            print("Scheduled tasks:")
            for job in cron_jobs:
                print(f"  - {job}")
        else:
            print("❌ Failed to setup cron jobs")
            
    except Exception as e:
        print(f"❌ Error setting up cron jobs: {e}")

def setup_windows_tasks():
    """Setup Windows Task Scheduler tasks"""
    try:
        # Create backup directory
        backup_dir = os.path.join(get_project_path(), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        tasks = create_windows_tasks()
        
        for task in tasks:
            # Create task using schtasks command
            cmd = [
                'schtasks', '/create',
                '/tn', task['name'],
                '/tr', f"cmd /c \"cd /d {get_project_path()} && {task['command']}\"",
                '/sc', task['schedule'],
                '/st', task['time'],
                '/f'  # Force overwrite if exists
            ]
            
            if task['schedule'] == 'HOURLY' and 'modifier' in task:
                cmd.extend(['/mo', task['modifier']])
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"✅ Created task: {task['name']}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to create task {task['name']}: {e}")
                print(f"   Error output: {e.stderr}")
        
        print("\n✅ Windows Task Scheduler setup complete!")
        print("You can view and manage tasks in Task Scheduler (taskschd.msc)")
        
    except Exception as e:
        print(f"❌ Error setting up Windows tasks: {e}")

def remove_cron_jobs():
    """Remove existing cron jobs"""
    system = platform.system().lower()
    
    if system in ['linux', 'darwin']:  # Linux or macOS
        try:
            current_cron = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode()
            
            # Remove lines containing 'deals89' or 'scheduler.py'
            new_cron = '\n'.join([
                line for line in current_cron.split('\n')
                if 'deals89' not in line.lower() and 'scheduler.py' not in line
            ])
            
            # Write new crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
            process.communicate(new_cron.encode())
            
            print("✅ Cron jobs removed successfully!")
            
        except subprocess.CalledProcessError:
            print("ℹ️  No existing cron jobs found")
        except Exception as e:
            print(f"❌ Error removing cron jobs: {e}")
    
    elif system == 'windows':
        tasks = ['Deals89_SocialPosting', 'Deals89_ExpireDeals', 'Deals89_Cleanup', 'Deals89_HealthCheck']
        
        for task_name in tasks:
            try:
                subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], 
                             capture_output=True, check=True)
                print(f"✅ Removed task: {task_name}")
            except subprocess.CalledProcessError:
                print(f"ℹ️  Task not found: {task_name}")

def main():
    """Main function to setup cron jobs based on the operating system"""
    if len(sys.argv) > 1 and sys.argv[1] == 'remove':
        print("Removing existing cron jobs/tasks...")
        remove_cron_jobs()
        return
    
    system = platform.system().lower()
    
    print(f"Setting up automated tasks for {platform.system()}...")
    print(f"Python path: {get_python_path()}")
    print(f"Project path: {get_project_path()}")
    print()
    
    if system in ['linux', 'darwin']:  # Linux or macOS
        setup_linux_cron()
    elif system == 'windows':
        setup_windows_tasks()
    else:
        print(f"❌ Unsupported operating system: {system}")
        print("Please set up scheduled tasks manually using your system's task scheduler.")
        return
    
    print("\n📋 Manual Setup Instructions:")
    print("1. Ensure all environment variables are set in .env file")
    print("2. Test individual commands manually first:")
    print("   python scheduler.py post")
    print("   python scheduler.py expire")
    print("   python scheduler.py cleanup")
    print("   python scheduler.py health")
    print("3. Check log files for any errors")
    print("4. Monitor the first few automated runs")

if __name__ == "__main__":
    main()