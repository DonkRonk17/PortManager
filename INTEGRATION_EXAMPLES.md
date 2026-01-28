# PortManager Integration Examples

> Real-world integration patterns with Team Brain tools

---

## Table of Contents

1. [SynapseLink Integration](#1-synapselink-integration)
2. [ConfigManager Integration](#2-configmanager-integration)
3. [TaskFlow Integration](#3-taskflow-integration)
4. [ErrorRecovery Integration](#4-errorrecovery-integration)
5. [LogHunter Integration](#5-loghunter-integration)
6. [TokenTracker Integration](#6-tokentracker-integration)
7. [BCH (Beacon Command Hub) Integration](#7-bch-beacon-command-hub-integration)
8. [CI/CD Pipeline Integration](#8-cicd-pipeline-integration)
9. [Monitoring Dashboard Integration](#9-monitoring-dashboard-integration)
10. [Multi-Agent Workflow Integration](#10-multi-agent-workflow-integration)

---

## 1. SynapseLink Integration

**Purpose:** Notify Team Brain agents when SSH connections are established.

### Basic Notification on Connect

```python
#!/usr/bin/env python3
"""
portmanager_synapse.py - PortManager with SynapseLink notifications
"""

from portmanager import connect, disconnect, load_profiles, show_active
from synapselink import quick_send, SynapseLink
from datetime import datetime

def connect_with_notification(profile: str, background: bool = True) -> bool:
    """Connect to SSH profile and notify team."""
    
    profiles = load_profiles()
    if profile not in profiles:
        quick_send(
            recipients="FORGE",
            subject=f"❌ SSH Profile Not Found: {profile}",
            content=f"Attempted to connect to '{profile}' but profile doesn't exist.\n"
                    f"Available profiles: {', '.join(profiles.keys())}",
            priority="HIGH"
        )
        return False
    
    try:
        result = connect(profile, background=background)
        
        if result:
            profile_data = profiles[profile]
            quick_send(
                recipients="FORGE,BOLT,NEXUS",
                subject=f"🔗 SSH Connected: {profile}",
                content=f"Connection established successfully!\n\n"
                        f"**Profile:** {profile}\n"
                        f"**Host:** {profile_data['user']}@{profile_data['host']}\n"
                        f"**Port:** {profile_data.get('port', 22)}\n"
                        f"**Forwards:** {len(profile_data.get('forwards', []))}\n"
                        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"**Background:** {background}",
                priority="LOW"
            )
        
        return result
        
    except Exception as e:
        quick_send(
            recipients="FORGE,BOLT",
            subject=f"❌ SSH Connection Failed: {profile}",
            content=f"Failed to connect to '{profile}'.\n\n"
                    f"**Error:** {str(e)}\n"
                    f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            priority="HIGH"
        )
        return False


def status_report():
    """Send status report of all active connections."""
    
    from portmanager import load_active
    active = load_active()
    
    if not active:
        content = "No active SSH connections."
    else:
        lines = ["**Active SSH Connections:**\n"]
        for name, data in active.items():
            profile = data['profile']
            started = data.get('started', 'Unknown')
            lines.append(f"- **{name}**: {profile['user']}@{profile['host']} (since {started})")
        content = '\n'.join(lines)
    
    quick_send(
        recipients="FORGE",
        subject="📊 SSH Connection Status Report",
        content=content,
        priority="LOW"
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'status':
            status_report()
        else:
            connect_with_notification(sys.argv[1])
```

---

## 2. ConfigManager Integration

**Purpose:** Centralize SSH profile configuration for multi-environment setups.

### Sync Profiles from ConfigManager

```python
#!/usr/bin/env python3
"""
sync_profiles.py - Sync SSH profiles from ConfigManager
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/ConfigManager")
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/PortManager")

from configmanager import ConfigManager
from portmanager import add_profile, add_forward, delete_profile, load_profiles

def sync_profiles_from_config(config_name: str = 'ssh-profiles'):
    """
    Sync SSH profiles from ConfigManager.
    
    Expected config structure:
    
    profiles:
      dev:
        host: dev.example.com
        user: developer
        port: 22
        key: ~/.ssh/dev_key
        forwards:
          - local: 5432
            remote: 5432
            host: localhost
            type: local
    """
    
    config = ConfigManager(config_name)
    config.load()
    
    config_profiles = config.get('profiles', {})
    current_profiles = load_profiles()
    
    # Track what we sync
    synced = []
    removed = []
    
    # Add/update profiles from config
    for name, profile_config in config_profiles.items():
        add_profile(
            name=name,
            host=profile_config['host'],
            user=profile_config['user'],
            port=profile_config.get('port', 22),
            key=profile_config.get('key')
        )
        
        # Add forwards
        for fwd in profile_config.get('forwards', []):
            add_forward(
                name=name,
                local_port=fwd['local'],
                remote_port=fwd['remote'],
                remote_host=fwd.get('host', 'localhost'),
                forward_type=fwd.get('type', 'local')
            )
        
        synced.append(name)
    
    # Remove profiles not in config (optional)
    if config.get('sync_mode') == 'strict':
        for name in current_profiles:
            if name not in config_profiles:
                delete_profile(name)
                removed.append(name)
    
    print(f"Synced {len(synced)} profiles: {', '.join(synced)}")
    if removed:
        print(f"Removed {len(removed)} profiles: {', '.join(removed)}")


def create_sample_config():
    """Create a sample SSH profiles config."""
    
    config = ConfigManager('ssh-profiles')
    
    config.set('profiles.dev', {
        'host': 'dev.example.com',
        'user': 'developer',
        'port': 22,
        'key': '~/.ssh/dev_key',
        'forwards': [
            {'local': 5432, 'remote': 5432, 'host': 'localhost', 'type': 'local'},
            {'local': 8000, 'remote': 8000, 'host': 'localhost', 'type': 'local'}
        ]
    })
    
    config.set('profiles.staging', {
        'host': 'staging.example.com',
        'user': 'deploy',
        'key': '~/.ssh/staging_key',
        'forwards': [
            {'local': 5433, 'remote': 5432, 'host': 'db.staging', 'type': 'local'}
        ]
    })
    
    config.set('profiles.prod', {
        'host': 'bastion.prod.com',
        'user': 'ops',
        'key': '~/.ssh/prod_key',
        'forwards': [
            {'local': 5434, 'remote': 5432, 'host': 'db.internal', 'type': 'local'},
            {'local': 6379, 'remote': 6379, 'host': 'redis.internal', 'type': 'local'}
        ]
    })
    
    config.save()
    print("Sample config created!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'sample':
        create_sample_config()
    else:
        sync_profiles_from_config()
```

---

## 3. TaskFlow Integration

**Purpose:** Include SSH connections as steps in automated workflows.

### Deployment Workflow

```python
#!/usr/bin/env python3
"""
deploy_workflow.py - Deployment workflow with PortManager
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/TaskFlow")
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/PortManager")

from taskflow import TaskFlow, Task
from portmanager import connect, disconnect, load_profiles, add_profile, add_forward
import subprocess
import time

class SSHConnectTask(Task):
    """Task to establish SSH connection."""
    
    def __init__(self, profile: str):
        super().__init__(name=f"SSH Connect: {profile}")
        self.profile = profile
    
    def run(self) -> dict:
        result = connect(self.profile, background=True)
        return {
            'success': result,
            'profile': self.profile,
            'message': f"Connected to {self.profile}" if result else f"Failed to connect to {self.profile}"
        }
    
    def rollback(self):
        disconnect(self.profile)


class RemoteCommandTask(Task):
    """Task to run command on remote server via tunnel."""
    
    def __init__(self, name: str, command: str, local_port: int = 22):
        super().__init__(name=name)
        self.command = command
        self.local_port = local_port
    
    def run(self) -> dict:
        full_cmd = ['ssh', '-p', str(self.local_port), 'localhost', self.command]
        result = subprocess.run(full_cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'command': self.command
        }


class DeployCodeTask(Task):
    """Task to deploy code via rsync."""
    
    def __init__(self, source: str, dest: str, local_port: int = 22):
        super().__init__(name="Deploy Code")
        self.source = source
        self.dest = dest
        self.local_port = local_port
    
    def run(self) -> dict:
        cmd = [
            'rsync', '-avz', '--delete',
            '-e', f'ssh -p {self.local_port}',
            self.source,
            f'localhost:{self.dest}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr
        }


def create_deployment_workflow(environment: str = 'staging'):
    """Create a deployment workflow."""
    
    # Ensure profile exists
    profiles = load_profiles()
    if f'{environment}-deploy' not in profiles:
        # Create default profile
        hosts = {
            'staging': 'staging.example.com',
            'prod': 'prod.example.com'
        }
        add_profile(f'{environment}-deploy', hosts.get(environment, 'localhost'), 'deploy')
        add_forward(f'{environment}-deploy', 2222, 22)  # SSH tunnel
    
    # Create workflow
    workflow = TaskFlow(f"Deploy to {environment.upper()}")
    
    # 1. Connect to server
    workflow.add_task(SSHConnectTask(f'{environment}-deploy'))
    
    # 2. Backup current version
    workflow.add_task(RemoteCommandTask(
        "Backup Current",
        "cd /app && cp -r current backup-$(date +%Y%m%d%H%M%S)",
        local_port=2222
    ))
    
    # 3. Deploy code
    workflow.add_task(DeployCodeTask(
        source='./dist/',
        dest='/app/current/',
        local_port=2222
    ))
    
    # 4. Install dependencies
    workflow.add_task(RemoteCommandTask(
        "Install Dependencies",
        "cd /app/current && pip install -r requirements.txt",
        local_port=2222
    ))
    
    # 5. Restart service
    workflow.add_task(RemoteCommandTask(
        "Restart Service",
        "sudo systemctl restart myapp",
        local_port=2222
    ))
    
    # 6. Health check
    workflow.add_task(RemoteCommandTask(
        "Health Check",
        "curl -f http://localhost:8000/health || exit 1",
        local_port=2222
    ))
    
    return workflow


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else 'staging'
    
    workflow = create_deployment_workflow(env)
    
    print(f"\n{'='*60}")
    print(f"Starting deployment to {env.upper()}")
    print(f"{'='*60}\n")
    
    results = workflow.run()
    
    print(f"\n{'='*60}")
    print("Deployment Complete!")
    print(f"{'='*60}")
    
    for task_name, result in results.items():
        status = "✓" if result.get('success') else "✗"
        print(f"  {status} {task_name}")
```

---

## 4. ErrorRecovery Integration

**Purpose:** Automatically recover from SSH connection failures.

### SSH Recovery Strategy

```python
#!/usr/bin/env python3
"""
ssh_recovery.py - ErrorRecovery integration for SSH connections
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/ErrorRecovery")
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/PortManager")

from errorrecovery import ErrorRecovery, RecoveryStrategy
from portmanager import connect, disconnect, load_profiles
import time
import subprocess

class SSHConnectionRecovery(RecoveryStrategy):
    """Recovery strategy for SSH connection failures."""
    
    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
    
    @property
    def name(self) -> str:
        return "SSH Connection Recovery"
    
    def can_handle(self, error: Exception, context: dict = None) -> bool:
        """Check if this strategy can handle the error."""
        error_str = str(error).lower()
        
        ssh_indicators = [
            'connection refused',
            'connection reset',
            'connection timed out',
            'ssh',
            'network unreachable',
            'host not found',
            'permission denied'
        ]
        
        return any(indicator in error_str for indicator in ssh_indicators)
    
    def recover(self, error: Exception, context: dict = None) -> bool:
        """Attempt to recover from SSH connection failure."""
        
        profile = context.get('profile') if context else None
        
        if not profile:
            print("[Recovery] No profile specified, cannot recover")
            return False
        
        print(f"[Recovery] Attempting to recover SSH connection to '{profile}'")
        
        for attempt in range(self.max_retries):
            wait_time = self.backoff_base ** attempt
            print(f"[Recovery] Attempt {attempt + 1}/{self.max_retries} (waiting {wait_time}s)")
            
            time.sleep(wait_time)
            
            try:
                # Clean up any existing connection
                disconnect(profile)
                time.sleep(1)
                
                # Test basic connectivity first
                profiles = load_profiles()
                if profile not in profiles:
                    print(f"[Recovery] Profile '{profile}' not found")
                    return False
                
                profile_data = profiles[profile]
                host = profile_data['host']
                
                # Ping test
                ping_result = subprocess.run(
                    ['ping', '-n', '1', '-w', '3000', host],
                    capture_output=True,
                    timeout=5
                )
                
                if ping_result.returncode != 0:
                    print(f"[Recovery] Host {host} not reachable")
                    continue
                
                # Try to connect
                if connect(profile, background=True):
                    print(f"[Recovery] Successfully reconnected to '{profile}'")
                    return True
                
            except Exception as e:
                print(f"[Recovery] Attempt {attempt + 1} failed: {e}")
                continue
        
        print(f"[Recovery] All attempts exhausted for '{profile}'")
        return False


def connect_with_recovery(profile: str, background: bool = True) -> bool:
    """Connect to SSH profile with automatic recovery."""
    
    recovery = ErrorRecovery()
    recovery.register_strategy(SSHConnectionRecovery())
    
    try:
        result = connect(profile, background=background)
        if not result:
            raise ConnectionError(f"SSH connection to '{profile}' failed")
        return True
        
    except Exception as e:
        # Attempt recovery
        recovered = recovery.handle_error(
            error=e,
            context={'profile': profile, 'background': background}
        )
        
        return recovered


if __name__ == "__main__":
    if len(sys.argv) > 1:
        profile = sys.argv[1]
        success = connect_with_recovery(profile)
        print(f"\nFinal status: {'Connected' if success else 'Failed'}")
    else:
        print("Usage: python ssh_recovery.py <profile_name>")
```

---

## 5. LogHunter Integration

**Purpose:** Monitor and analyze SSH connection logs.

### SSH Log Analysis

```python
#!/usr/bin/env python3
"""
ssh_log_analysis.py - Monitor SSH connections with LogHunter
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/LogHunter")
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/PortManager")

from loghunter import LogHunter
from portmanager import CONFIG_DIR
from datetime import datetime, timedelta
from pathlib import Path

# Enable logging in PortManager (add this to portmanager.py)
LOG_FILE = CONFIG_DIR / 'portmanager.log'


def analyze_ssh_logs(hours: int = 24):
    """Analyze SSH connection logs from the past N hours."""
    
    hunter = LogHunter()
    
    # Add PortManager log as source
    if LOG_FILE.exists():
        hunter.add_source(str(LOG_FILE))
    
    # Add system SSH log (Linux/macOS)
    system_logs = [
        '/var/log/auth.log',      # Ubuntu/Debian
        '/var/log/secure',        # RHEL/CentOS
        '~/.ssh/logs'             # Custom SSH logs
    ]
    
    for log in system_logs:
        path = Path(log).expanduser()
        if path.exists():
            hunter.add_source(str(path))
    
    # Search patterns
    analysis = {
        'connections': [],
        'failures': [],
        'forwards': [],
        'errors': []
    }
    
    since = datetime.now() - timedelta(hours=hours)
    
    # Find successful connections
    connections = hunter.search(
        pattern=r"(connected|Connection established|Connecting to)",
        case_insensitive=True,
        since=since
    )
    analysis['connections'] = connections
    
    # Find failed connections
    failures = hunter.search(
        pattern=r"(connection refused|permission denied|timed out|failed)",
        case_insensitive=True,
        since=since
    )
    analysis['failures'] = failures
    
    # Find port forward activity
    forwards = hunter.search(
        pattern=r"(-L|-R|forward|tunnel)",
        case_insensitive=True,
        since=since
    )
    analysis['forwards'] = forwards
    
    # Find errors
    errors = hunter.search(
        pattern=r"(error|exception|warning)",
        case_insensitive=True,
        since=since
    )
    analysis['errors'] = errors
    
    return analysis


def print_report(analysis: dict):
    """Print analysis report."""
    
    print("\n" + "="*60)
    print("SSH CONNECTION ANALYSIS REPORT")
    print("="*60)
    
    print(f"\n📊 Summary (last 24 hours):")
    print(f"   Successful connections: {len(analysis['connections'])}")
    print(f"   Failed connections: {len(analysis['failures'])}")
    print(f"   Port forwards: {len(analysis['forwards'])}")
    print(f"   Errors/Warnings: {len(analysis['errors'])}")
    
    if analysis['failures']:
        print(f"\n❌ Recent Failures:")
        for failure in analysis['failures'][:5]:
            print(f"   - {failure.timestamp}: {failure.message[:60]}...")
    
    if analysis['errors']:
        print(f"\n⚠️ Recent Errors:")
        for error in analysis['errors'][:5]:
            print(f"   - {error.timestamp}: {error.message[:60]}...")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    analysis = analyze_ssh_logs(hours)
    print_report(analysis)
```

---

## 6. TokenTracker Integration

**Purpose:** Track costs associated with cloud SSH resources.

### SSH Usage Cost Tracking

```python
#!/usr/bin/env python3
"""
ssh_cost_tracker.py - Track SSH-related costs with TokenTracker
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/TokenTracker")
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/PortManager")

from tokentracker import TokenTracker
from portmanager import load_profiles, load_active
from datetime import datetime, timedelta

# Define cost models for different server types
COST_MODELS = {
    'ec2-small': 0.0116,      # $/hour for t3.micro
    'ec2-medium': 0.0464,     # $/hour for t3.medium
    'ec2-large': 0.0928,      # $/hour for t3.large
    'bastion': 0.05,          # Fixed cost per connection hour
    'default': 0.02           # Default cost estimate
}


def track_ssh_costs():
    """Track costs for SSH connections."""
    
    tracker = TokenTracker()
    active = load_active()
    profiles = load_profiles()
    
    total_cost = 0.0
    
    for name, connection in active.items():
        started = datetime.fromisoformat(connection.get('started', datetime.now().isoformat()))
        duration_hours = (datetime.now() - started).total_seconds() / 3600
        
        # Get cost model based on profile metadata
        profile = profiles.get(name, {})
        server_type = profile.get('metadata', {}).get('server_type', 'default')
        cost_per_hour = COST_MODELS.get(server_type, COST_MODELS['default'])
        
        connection_cost = duration_hours * cost_per_hour
        total_cost += connection_cost
        
        # Log to TokenTracker
        tracker.log_usage(
            service='ssh',
            operation=f'connection:{name}',
            units=duration_hours,
            cost=connection_cost,
            metadata={
                'profile': name,
                'host': profile.get('host'),
                'server_type': server_type,
                'forwards': len(profile.get('forwards', []))
            }
        )
    
    return total_cost


def monthly_ssh_report():
    """Generate monthly SSH cost report."""
    
    tracker = TokenTracker()
    
    # Get this month's SSH usage
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    usage = tracker.get_usage(
        service='ssh',
        since=start_of_month
    )
    
    total_hours = sum(u.get('units', 0) for u in usage)
    total_cost = sum(u.get('cost', 0) for u in usage)
    
    # Group by profile
    by_profile = {}
    for u in usage:
        profile = u.get('metadata', {}).get('profile', 'unknown')
        if profile not in by_profile:
            by_profile[profile] = {'hours': 0, 'cost': 0}
        by_profile[profile]['hours'] += u.get('units', 0)
        by_profile[profile]['cost'] += u.get('cost', 0)
    
    print("\n" + "="*60)
    print(f"SSH COST REPORT - {now.strftime('%B %Y')}")
    print("="*60)
    print(f"\nTotal Hours: {total_hours:.2f}")
    print(f"Total Cost:  ${total_cost:.2f}")
    print(f"\nBy Profile:")
    
    for profile, data in sorted(by_profile.items(), key=lambda x: -x[1]['cost']):
        print(f"  {profile}: {data['hours']:.2f} hours = ${data['cost']:.2f}")
    
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'report':
        monthly_ssh_report()
    else:
        cost = track_ssh_costs()
        print(f"Current session cost: ${cost:.4f}")
```

---

## 7. BCH (Beacon Command Hub) Integration

**Purpose:** Integrate PortManager with BCH for remote server management.

### BCH Connection Manager

```python
#!/usr/bin/env python3
"""
bch_connections.py - BCH server connection management
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/PortManager")
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/SynapseLink")

from portmanager import (
    add_profile, add_forward, connect, disconnect,
    load_profiles, list_profiles, show_active
)
from synapselink import quick_send
from datetime import datetime

# BCH Server Configurations
BCH_SERVERS = {
    'bch-dev': {
        'host': 'bch-dev.beacon-hq.local',
        'user': 'logan',
        'key': '~/.ssh/bch_dev',
        'forwards': [
            {'local': 8080, 'remote': 8080, 'host': 'localhost'},    # Frontend
            {'local': 5001, 'remote': 5001, 'host': 'localhost'},    # Backend
            {'local': 5432, 'remote': 5432, 'host': 'localhost'},    # PostgreSQL
        ]
    },
    'bch-staging': {
        'host': 'bch-staging.beacon-hq.com',
        'user': 'deploy',
        'key': '~/.ssh/bch_staging',
        'forwards': [
            {'local': 8081, 'remote': 8080, 'host': 'localhost'},
            {'local': 5002, 'remote': 5001, 'host': 'localhost'},
            {'local': 5433, 'remote': 5432, 'host': 'postgres.internal'},
        ]
    },
    'bch-prod': {
        'host': 'bastion.beacon-hq.com',
        'user': 'ops',
        'key': '~/.ssh/bch_prod',
        'forwards': [
            {'local': 8082, 'remote': 8080, 'host': 'bch-app.internal'},
            {'local': 5003, 'remote': 5001, 'host': 'bch-api.internal'},
            {'local': 5434, 'remote': 5432, 'host': 'bch-db.internal'},
            {'local': 6379, 'remote': 6379, 'host': 'bch-redis.internal'},
        ]
    }
}


def setup_bch_profiles():
    """Initialize all BCH server profiles."""
    
    for name, config in BCH_SERVERS.items():
        # Add profile
        add_profile(
            name=name,
            host=config['host'],
            user=config['user'],
            key=config.get('key')
        )
        
        # Add forwards
        for fwd in config.get('forwards', []):
            add_forward(
                name=name,
                local_port=fwd['local'],
                remote_port=fwd['remote'],
                remote_host=fwd.get('host', 'localhost')
            )
    
    print(f"✓ Set up {len(BCH_SERVERS)} BCH profiles")


def connect_bch(environment: str = 'dev'):
    """Connect to a BCH environment."""
    
    profile = f'bch-{environment}'
    
    profiles = load_profiles()
    if profile not in profiles:
        print(f"Profile '{profile}' not found. Running setup...")
        setup_bch_profiles()
    
    print(f"\n{'='*50}")
    print(f"Connecting to BCH {environment.upper()}")
    print(f"{'='*50}")
    
    result = connect(profile, background=True)
    
    if result:
        config = BCH_SERVERS.get(profile, {})
        
        print(f"\n✓ Connected to {config.get('host')}")
        print(f"\nAvailable Services (localhost):")
        
        for fwd in config.get('forwards', []):
            service = 'Unknown'
            if fwd['remote'] == 8080:
                service = 'Frontend'
            elif fwd['remote'] == 5001:
                service = 'Backend API'
            elif fwd['remote'] == 5432:
                service = 'PostgreSQL'
            elif fwd['remote'] == 6379:
                service = 'Redis'
            
            print(f"  - {service}: localhost:{fwd['local']}")
        
        # Notify team
        quick_send(
            recipients="FORGE,BOLT",
            subject=f"🔗 BCH {environment.upper()} Connected",
            content=f"Logan connected to BCH {environment}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    f"Services: {len(config.get('forwards', []))} ports forwarded",
            priority="LOW"
        )
    else:
        print(f"\n✗ Failed to connect")
    
    return result


def bch_status():
    """Show BCH connection status."""
    
    print("\n" + "="*50)
    print("BCH CONNECTION STATUS")
    print("="*50)
    
    from portmanager import load_active
    active = load_active()
    
    for env in ['dev', 'staging', 'prod']:
        profile = f'bch-{env}'
        status = "🟢 CONNECTED" if profile in active else "⚪ Disconnected"
        print(f"  {env.upper():10} {status}")
    
    print("="*50)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'setup':
            setup_bch_profiles()
        elif cmd == 'status':
            bch_status()
        elif cmd in ['dev', 'staging', 'prod']:
            connect_bch(cmd)
        elif cmd == 'list':
            list_profiles()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: bch_connections.py [setup|status|dev|staging|prod|list]")
    else:
        print("BCH Connection Manager")
        print("Usage: bch_connections.py [setup|status|dev|staging|prod|list]")
```

---

## 8. CI/CD Pipeline Integration

**Purpose:** Use PortManager in automated deployment pipelines.

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy with SSH Tunnels

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install paramiko
          git clone https://github.com/DonkRonk17/PortManager.git
      
      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          echo "${{ secrets.SSH_KNOWN_HOSTS }}" >> ~/.ssh/known_hosts
      
      - name: Set up tunnel and deploy
        run: |
          python - << 'EOF'
          import sys
          sys.path.insert(0, 'PortManager')
          
          from portmanager import add_profile, add_forward, connect
          import subprocess
          import time
          
          # Configure profile
          add_profile(
              'deploy-server',
              '${{ secrets.DEPLOY_HOST }}',
              '${{ secrets.DEPLOY_USER }}',
              key='~/.ssh/deploy_key'
          )
          add_forward('deploy-server', 2222, 22)
          
          # Connect
          connect('deploy-server', background=True)
          time.sleep(2)  # Wait for tunnel
          
          # Deploy via tunnel
          subprocess.run([
              'rsync', '-avz', '--delete',
              '-e', 'ssh -p 2222 -o StrictHostKeyChecking=no',
              './dist/',
              'localhost:/app/current/'
          ], check=True)
          
          # Restart service
          subprocess.run([
              'ssh', '-p', '2222',
              '-o', 'StrictHostKeyChecking=no',
              'localhost',
              'sudo systemctl restart myapp'
          ], check=True)
          
          print('Deployment complete!')
          EOF
```

---

## 9. Monitoring Dashboard Integration

**Purpose:** Display SSH connection status in monitoring dashboards.

### Prometheus Metrics Exporter

```python
#!/usr/bin/env python3
"""
ssh_metrics.py - Export SSH connection metrics for Prometheus
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/PortManager")

from portmanager import load_profiles, load_active
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

METRICS_PORT = 9100


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics."""
    
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            
            metrics = generate_metrics()
            self.wfile.write(metrics.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def generate_metrics() -> str:
    """Generate Prometheus metrics."""
    
    profiles = load_profiles()
    active = load_active()
    
    lines = []
    
    # Total profiles
    lines.append("# HELP ssh_profiles_total Total number of SSH profiles")
    lines.append("# TYPE ssh_profiles_total gauge")
    lines.append(f"ssh_profiles_total {len(profiles)}")
    
    # Active connections
    lines.append("# HELP ssh_connections_active Current active SSH connections")
    lines.append("# TYPE ssh_connections_active gauge")
    lines.append(f"ssh_connections_active {len(active)}")
    
    # Connection duration
    lines.append("# HELP ssh_connection_duration_seconds Duration of active connections")
    lines.append("# TYPE ssh_connection_duration_seconds gauge")
    
    for name, conn in active.items():
        started = datetime.fromisoformat(conn.get('started', datetime.now().isoformat()))
        duration = (datetime.now() - started).total_seconds()
        lines.append(f'ssh_connection_duration_seconds{{profile="{name}"}} {duration}')
    
    # Port forwards
    lines.append("# HELP ssh_port_forwards_total Total port forwards across all profiles")
    lines.append("# TYPE ssh_port_forwards_total gauge")
    
    total_forwards = sum(len(p.get('forwards', [])) for p in profiles.values())
    lines.append(f"ssh_port_forwards_total {total_forwards}")
    
    # Per-profile metrics
    lines.append("# HELP ssh_profile_forwards_count Number of forwards per profile")
    lines.append("# TYPE ssh_profile_forwards_count gauge")
    
    for name, profile in profiles.items():
        forwards = len(profile.get('forwards', []))
        lines.append(f'ssh_profile_forwards_count{{profile="{name}"}} {forwards}')
    
    return '\n'.join(lines) + '\n'


def run_metrics_server():
    """Run the metrics HTTP server."""
    
    server = HTTPServer(('0.0.0.0', METRICS_PORT), MetricsHandler)
    print(f"SSH metrics server running on http://localhost:{METRICS_PORT}/metrics")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_metrics_server()
```

---

## 10. Multi-Agent Workflow Integration

**Purpose:** Coordinate SSH connections across Team Brain agents.

### Multi-Agent SSH Coordinator

```python
#!/usr/bin/env python3
"""
multi_agent_ssh.py - Coordinate SSH across Team Brain agents
"""

import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/PortManager")
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/SynapseLink")

from portmanager import (
    add_profile, add_forward, connect, disconnect,
    load_profiles, load_active, save_active
)
from synapselink import SynapseLink, quick_send
from datetime import datetime
import json
import time

class SSHCoordinator:
    """Coordinates SSH connections for Team Brain agents."""
    
    def __init__(self):
        self.synapse = SynapseLink()
        self.agent_locks = {}
    
    def request_connection(self, agent: str, profile: str) -> bool:
        """
        Request exclusive connection to a profile.
        Prevents multiple agents from connecting to same server.
        """
        
        active = load_active()
        
        # Check if already in use
        if profile in active:
            owner = active[profile].get('metadata', {}).get('agent', 'unknown')
            if owner != agent:
                self._notify_conflict(agent, profile, owner)
                return False
        
        # Grant connection
        try:
            result = connect(profile, background=True)
            
            if result:
                # Record agent ownership
                active = load_active()
                if profile in active:
                    active[profile]['metadata'] = {
                        'agent': agent,
                        'acquired': datetime.now().isoformat()
                    }
                    save_active(active)
                
                self._notify_acquired(agent, profile)
                return True
            
            return False
            
        except Exception as e:
            self._notify_error(agent, profile, str(e))
            return False
    
    def release_connection(self, agent: str, profile: str) -> bool:
        """Release connection back to pool."""
        
        active = load_active()
        
        if profile not in active:
            return True  # Already released
        
        owner = active[profile].get('metadata', {}).get('agent')
        if owner and owner != agent:
            print(f"Warning: {agent} trying to release {profile} owned by {owner}")
            return False
        
        disconnect(profile)
        self._notify_released(agent, profile)
        return True
    
    def get_available_profiles(self, agent: str) -> list:
        """Get profiles available for an agent to connect to."""
        
        profiles = load_profiles()
        active = load_active()
        
        available = []
        for name in profiles:
            if name not in active:
                available.append(name)
            elif active[name].get('metadata', {}).get('agent') == agent:
                available.append(name)  # Agent's own connection
        
        return available
    
    def _notify_conflict(self, agent: str, profile: str, owner: str):
        """Notify agent about connection conflict."""
        quick_send(
            recipients=agent,
            subject=f"⚠️ SSH Conflict: {profile}",
            content=f"Cannot connect to '{profile}'.\n"
                    f"Currently in use by: {owner}\n"
                    f"Please wait or use a different profile.",
            priority="NORMAL"
        )
    
    def _notify_acquired(self, agent: str, profile: str):
        """Notify about successful connection."""
        quick_send(
            recipients="FORGE",
            subject=f"🔗 SSH Acquired: {profile}",
            content=f"Agent: {agent}\n"
                    f"Profile: {profile}\n"
                    f"Time: {datetime.now().strftime('%H:%M:%S')}",
            priority="LOW"
        )
    
    def _notify_released(self, agent: str, profile: str):
        """Notify about connection release."""
        quick_send(
            recipients="FORGE",
            subject=f"🔓 SSH Released: {profile}",
            content=f"Agent: {agent}\n"
                    f"Profile: {profile}\n"
                    f"Time: {datetime.now().strftime('%H:%M:%S')}",
            priority="LOW"
        )
    
    def _notify_error(self, agent: str, profile: str, error: str):
        """Notify about connection error."""
        quick_send(
            recipients=f"{agent},FORGE",
            subject=f"❌ SSH Error: {profile}",
            content=f"Agent: {agent}\n"
                    f"Profile: {profile}\n"
                    f"Error: {error}",
            priority="HIGH"
        )


# Example usage
if __name__ == "__main__":
    coordinator = SSHCoordinator()
    
    # Simulate BOLT requesting a connection
    print("BOLT requesting bch-dev...")
    success = coordinator.request_connection("BOLT", "bch-dev")
    print(f"Result: {'✓ Granted' if success else '✗ Denied'}")
    
    # Check available profiles
    print(f"\nProfiles available to NEXUS: {coordinator.get_available_profiles('NEXUS')}")
    
    # Release connection
    time.sleep(2)
    print("\nBOLT releasing bch-dev...")
    coordinator.release_connection("BOLT", "bch-dev")
```

---

## Summary

These integration examples demonstrate how PortManager can be combined with:

| Tool | Integration Purpose |
|------|---------------------|
| SynapseLink | Team notifications |
| ConfigManager | Centralized configuration |
| TaskFlow | Automated workflows |
| ErrorRecovery | Automatic reconnection |
| LogHunter | Log analysis |
| TokenTracker | Cost tracking |
| BCH | Server management |
| CI/CD | Deployment pipelines |
| Prometheus | Monitoring metrics |
| Multi-Agent | Team coordination |

---

**Built by:** FORGE (Team Brain)  
**For:** Logan Smith / Metaphy LLC  
**Date:** January 2026
