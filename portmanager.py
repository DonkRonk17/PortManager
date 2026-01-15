#!/usr/bin/env python3
"""
PortManager - Smart SSH Connection & Port Forwarding Manager
=============================================================
Save and manage SSH connections with port forwards. Never type SSH commands again!

Features:
- Save SSH connection profiles (host, user, key)
- Manage local/remote port forwards
- Quick connect with profiles
- List active connections
- Zero dependencies (pure Python)

Author: Holy Grail Automation
Version: 1.0.0
"""

import os
import sys
import json
import subprocess
import argparse
import platform
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

HOME = Path.home()
CONFIG_DIR = HOME / '.portmanager'
PROFILES_FILE = CONFIG_DIR / 'profiles.json'
ACTIVE_FILE = CONFIG_DIR / 'active_connections.json'

# ============================================================================
# UTILITIES
# ============================================================================

def ensure_config_dir():
    """Ensure configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_profiles():
    """Load saved SSH profiles."""
    if not PROFILES_FILE.exists():
        return {}
    try:
        with open(PROFILES_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_profiles(profiles):
    """Save SSH profiles to disk."""
    ensure_config_dir()
    with open(PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)

def load_active():
    """Load active connection info."""
    if not ACTIVE_FILE.exists():
        return {}
    try:
        with open(ACTIVE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_active(active):
    """Save active connection info."""
    ensure_config_dir()
    with open(ACTIVE_FILE, 'w') as f:
        json.dump(active, f, indent=2)

# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================

def add_profile(name, host, user, port=22, key=None, forwards=None):
    """Add or update an SSH profile."""
    profiles = load_profiles()
    
    profile = {
        'host': host,
        'user': user,
        'port': port,
        'created': datetime.now().isoformat(),
        'last_used': None
    }
    
    if key:
        profile['key'] = key
    
    if forwards:
        profile['forwards'] = forwards
    else:
        profile['forwards'] = []
    
    profiles[name] = profile
    save_profiles(profiles)
    
    print(f"[OK] Profile '{name}' saved!")
    print(f"  {user}@{host}:{port}")
    if key:
        print(f"  Key: {key}")
    if profile['forwards']:
        print(f"  Forwards: {len(profile['forwards'])} configured")

def list_profiles():
    """List all saved profiles."""
    profiles = load_profiles()
    
    if not profiles:
        print("No profiles saved yet.")
        print("\nCreate one with:")
        print("  portmanager add myserver user@host.com")
        return
    
    print(f"\n[*] Saved Profiles ({len(profiles)}):\n")
    
    for name, prof in sorted(profiles.items()):
        user = prof['user']
        host = prof['host']
        port = prof.get('port', 22)
        key = prof.get('key', 'password')
        forwards = prof.get('forwards', [])
        last_used = prof.get('last_used', 'never')
        
        if last_used and last_used != 'never':
            try:
                last_used = datetime.fromisoformat(last_used).strftime('%Y-%m-%d %H:%M')
            except:
                last_used = 'never'
        else:
            last_used = 'never'
        
        print(f"  {name}")
        print(f"    Connection: {user}@{host}:{port}")
        print(f"    Auth: {'Key: ' + key if key != 'password' else 'Password'}")
        
        if forwards:
            print(f"    Forwards:")
            for fwd in forwards:
                fwd_type = fwd.get('type', 'local')
                local = fwd.get('local_port')
                remote = fwd.get('remote_port')
                remote_host = fwd.get('remote_host', 'localhost')
                
                if fwd_type == 'local':
                    print(f"      L: localhost:{local} -> {remote_host}:{remote}")
                else:
                    print(f"      R: {remote_host}:{remote} -> localhost:{local}")
        
        print(f"    Last used: {last_used}")
        print()

def delete_profile(name):
    """Delete a saved profile."""
    profiles = load_profiles()
    
    if name not in profiles:
        print(f"[X] Profile '{name}' not found.")
        return False
    
    del profiles[name]
    save_profiles(profiles)
    print(f"[OK] Profile '{name}' deleted.")
    return True

def add_forward(profile_name, local_port, remote_port, remote_host='localhost', forward_type='local'):
    """Add a port forward to a profile."""
    profiles = load_profiles()
    
    if profile_name not in profiles:
        print(f"[X] Profile '{profile_name}' not found.")
        return False
    
    forward = {
        'type': forward_type,
        'local_port': int(local_port),
        'remote_port': int(remote_port),
        'remote_host': remote_host
    }
    
    if 'forwards' not in profiles[profile_name]:
        profiles[profile_name]['forwards'] = []
    
    profiles[profile_name]['forwards'].append(forward)
    save_profiles(profiles)
    
    fwd_str = f"localhost:{local_port} -> {remote_host}:{remote_port}" if forward_type == 'local' else f"{remote_host}:{remote_port} -> localhost:{local_port}"
    print(f"[OK] Added {forward_type} forward to '{profile_name}': {fwd_str}")
    return True

# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

def build_ssh_command(profile):
    """Build SSH command from profile."""
    cmd = ['ssh']
    
    # Add port
    if profile.get('port', 22) != 22:
        cmd.extend(['-p', str(profile['port'])])
    
    # Add key if specified
    if 'key' in profile and profile['key']:
        key_path = os.path.expanduser(profile['key'])
        if os.path.exists(key_path):
            cmd.extend(['-i', key_path])
    
    # Add port forwards
    forwards = profile.get('forwards', [])
    for fwd in forwards:
        fwd_type = fwd.get('type', 'local')
        local = fwd['local_port']
        remote = fwd['remote_port']
        remote_host = fwd.get('remote_host', 'localhost')
        
        if fwd_type == 'local':
            # Local forward: -L local_port:remote_host:remote_port
            cmd.extend(['-L', f"{local}:{remote_host}:{remote}"])
        else:
            # Remote forward: -R remote_port:localhost:local_port
            cmd.extend(['-R', f"{remote}:{remote_host}:{local}"])
    
    # Add connection string
    cmd.append(f"{profile['user']}@{profile['host']}")
    
    return cmd

def connect(profile_name, background=False):
    """Connect using a saved profile."""
    profiles = load_profiles()
    
    if profile_name not in profiles:
        print(f"[X] Profile '{profile_name}' not found.")
        print("\nAvailable profiles:")
        for name in sorted(profiles.keys()):
            print(f"  - {name}")
        return False
    
    profile = profiles[profile_name]
    cmd = build_ssh_command(profile)
    
    # Update last used
    profile['last_used'] = datetime.now().isoformat()
    profiles[profile_name] = profile
    save_profiles(profiles)
    
    # Show connection info
    print(f"\n[*] Connecting to '{profile_name}'...")
    print(f"   {profile['user']}@{profile['host']}:{profile.get('port', 22)}")
    
    forwards = profile.get('forwards', [])
    if forwards:
        print(f"\n[>] Port Forwards:")
        for fwd in forwards:
            fwd_type = fwd.get('type', 'local')
            local = fwd['local_port']
            remote = fwd['remote_port']
            remote_host = fwd.get('remote_host', 'localhost')
            
            if fwd_type == 'local':
                print(f"   L: localhost:{local} -> {remote_host}:{remote}")
            else:
                print(f"   R: {remote_host}:{remote} -> localhost:{local}")
    
    print(f"\n[>] Command: {' '.join(cmd)}\n")
    
    if background:
        # Run in background (non-blocking)
        if platform.system() == 'Windows':
            # Windows: use START
            subprocess.Popen(['start', 'cmd', '/k'] + cmd, shell=True)
        else:
            # Unix: run with nohup
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("[OK] Connection started in background")
        
        # Track active connection
        active = load_active()
        active[profile_name] = {
            'started': datetime.now().isoformat(),
            'profile': profile
        }
        save_active(active)
    else:
        # Run interactively
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n[OK] Connection closed")
        except Exception as e:
            print(f"\n[X] Error: {e}")
            return False
    
    return True

def show_active():
    """Show active background connections."""
    active = load_active()
    
    if not active:
        print("No active background connections.")
        return
    
    print(f"\n[*] Active Connections ({len(active)}):\n")
    
    for name, info in active.items():
        started = datetime.fromisoformat(info['started']).strftime('%Y-%m-%d %H:%M')
        profile = info['profile']
        
        print(f"  {name}")
        print(f"    {profile['user']}@{profile['host']}:{profile.get('port', 22)}")
        print(f"    Started: {started}")
        
        forwards = profile.get('forwards', [])
        if forwards:
            for fwd in forwards:
                fwd_type = fwd.get('type', 'local')
                local = fwd['local_port']
                remote = fwd['remote_port']
                remote_host = fwd.get('remote_host', 'localhost')
                
                if fwd_type == 'local':
                    print(f"      L: localhost:{local} -> {remote_host}:{remote}")
                else:
                    print(f"      R: {remote_host}:{remote} -> localhost:{local}")
        print()

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description='PortManager - Smart SSH Connection & Port Forwarding Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a simple SSH profile
  portmanager add myserver user@example.com
  
  # Add profile with custom port and key
  portmanager add myserver user@example.com --port 2222 --key ~/.ssh/id_rsa
  
  # Add port forward to profile
  portmanager forward myserver 8080 80
  
  # Add remote port forward
  portmanager forward myserver 3000 3000 --remote
  
  # Connect to server
  portmanager connect myserver
  
  # Connect in background
  portmanager connect myserver --background
  
  # List all profiles
  portmanager list
  
  # Show active connections
  portmanager active
  
  # Delete profile
  portmanager delete myserver
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add profile
    add_parser = subparsers.add_parser('add', help='Add or update SSH profile')
    add_parser.add_argument('name', help='Profile name')
    add_parser.add_argument('connection', help='user@host')
    add_parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
    add_parser.add_argument('--key', help='Path to SSH private key')
    
    # List profiles
    subparsers.add_parser('list', help='List all saved profiles')
    
    # Delete profile
    del_parser = subparsers.add_parser('delete', help='Delete a profile')
    del_parser.add_argument('name', help='Profile name to delete')
    
    # Add forward
    fwd_parser = subparsers.add_parser('forward', help='Add port forward to profile')
    fwd_parser.add_argument('profile', help='Profile name')
    fwd_parser.add_argument('local_port', type=int, help='Local port')
    fwd_parser.add_argument('remote_port', type=int, help='Remote port')
    fwd_parser.add_argument('--host', default='localhost', help='Remote host (default: localhost)')
    fwd_parser.add_argument('--remote', action='store_true', help='Remote forward (default: local)')
    
    # Connect
    conn_parser = subparsers.add_parser('connect', help='Connect using profile')
    conn_parser.add_argument('name', help='Profile name')
    conn_parser.add_argument('--background', '-b', action='store_true', help='Run in background')
    
    # Show active
    subparsers.add_parser('active', help='Show active connections')
    
    # Parse args
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    try:
        if args.command == 'add':
            # Parse user@host
            if '@' not in args.connection:
                print("[X] Connection must be in format: user@host")
                return 1
            
            user, host = args.connection.split('@', 1)
            add_profile(args.name, host, user, args.port, args.key)
        
        elif args.command == 'list':
            list_profiles()
        
        elif args.command == 'delete':
            delete_profile(args.name)
        
        elif args.command == 'forward':
            fwd_type = 'remote' if args.remote else 'local'
            add_forward(args.profile, args.local_port, args.remote_port, args.host, fwd_type)
        
        elif args.command == 'connect':
            connect(args.name, args.background)
        
        elif args.command == 'active':
            show_active()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
