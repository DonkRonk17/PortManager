# PortManager Integration Plan

> Comprehensive guide for integrating PortManager into Team Brain workflows

---

## Overview

**Tool:** PortManager  
**Version:** 1.0  
**Purpose:** Manage SSH connections and port forwards with saved profiles  
**Integration Status:** Phase 7 Complete  

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TEAM BRAIN ECOSYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐    ┌──────────────┐    ┌───────────────────┐    │
│  │   FORGE   │    │   TaskFlow   │    │  SynapseLink      │    │
│  │ (Planner) │    │  (Workflow)  │    │  (Notifications)  │    │
│  └─────┬─────┘    └──────┬───────┘    └─────────┬─────────┘    │
│        │                 │                       │              │
│        ▼                 ▼                       ▼              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    PORTMANAGER                               ││
│  │  • Profile Management  • Port Forwards  • SSH Connections   ││
│  └─────────────────────────────────────────────────────────────┘│
│        │                 │                       │              │
│        ▼                 ▼                       ▼              │
│  ┌───────────┐    ┌──────────────┐    ┌───────────────────┐    │
│  │ ConfigMgr │    │   LogHunter  │    │  ErrorRecovery    │    │
│  │ (Config)  │    │   (Logs)     │    │  (Monitoring)     │    │
│  └───────────┘    └──────────────┘    └───────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### 1. ConfigManager Integration

**Purpose:** Use ConfigManager for centralized SSH profile configuration.

**Setup:**

```python
from configmanager import ConfigManager
from portmanager import add_profile, add_forward

# Load SSH configurations from central config
config = ConfigManager('ssh-profiles')
config.load()

# Sync profiles from ConfigManager
for name, profile in config.get('profiles', {}).items():
    add_profile(
        name=name,
        host=profile['host'],
        user=profile['user'],
        port=profile.get('port', 22),
        key=profile.get('key')
    )
    
    # Add forwards
    for fwd in profile.get('forwards', []):
        add_forward(
            name=name,
            local_port=fwd['local'],
            remote_port=fwd['remote'],
            remote_host=fwd.get('host', 'localhost'),
            forward_type=fwd.get('type', 'local')
        )
```

**Config File Example (ssh-profiles.yaml):**

```yaml
profiles:
  bch-server:
    host: bch.beacon-hq.com
    user: logan
    port: 22
    key: ~/.ssh/bch_key
    forwards:
      - local: 8080
        remote: 8080
        type: local
      - local: 5001
        remote: 5001
        type: local
        
  prod-db:
    host: db.production.com
    user: dbadmin
    key: ~/.ssh/prod_key
    forwards:
      - local: 5432
        remote: 5432
        host: postgres.internal
```

---

### 2. TaskFlow Integration

**Purpose:** Include SSH connections in automated workflows.

**Example Workflow:**

```yaml
# taskflow workflow: deploy-backend.yaml
workflow:
  name: Deploy Backend
  
  steps:
    - name: Establish Tunnel
      tool: portmanager
      action: connect
      profile: prod-server
      background: true
      
    - name: Deploy Code
      tool: shell
      command: rsync -avz ./dist/ localhost:8022:/app/
      
    - name: Restart Service
      tool: shell
      command: ssh -p 8022 localhost 'sudo systemctl restart backend'
```

**Python Implementation:**

```python
from taskflow import Task, Workflow
from portmanager import connect, disconnect

class SSHConnectionTask(Task):
    """Task for managing SSH connections in workflows."""
    
    def __init__(self, profile: str, background: bool = True):
        self.profile = profile
        self.background = background
    
    def run(self):
        connect(self.profile, background=self.background)
        return True
    
    def cleanup(self):
        disconnect(self.profile)

# Use in workflow
workflow = Workflow("deployment")
workflow.add_task(SSHConnectionTask("prod-server"))
workflow.add_task(ShellTask("rsync -avz ./dist/ localhost:8022:/app/"))
workflow.run()
```

---

### 3. SynapseLink Integration

**Purpose:** Notify team when connections are established/failed.

**Implementation:**

```python
from synapselink import quick_send
from portmanager import connect, show_active

def connect_with_notification(profile: str, notify_team: bool = True):
    """Connect to profile and notify team."""
    try:
        result = connect(profile, background=True)
        
        if result and notify_team:
            quick_send(
                recipients="FORGE,BOLT,NEXUS",
                subject=f"🔗 SSH Connection: {profile}",
                content=f"Connection established to {profile}\n"
                        f"Status: ACTIVE\n"
                        f"Forwards: {get_forward_count(profile)}",
                priority="LOW"
            )
        
        return result
        
    except Exception as e:
        if notify_team:
            quick_send(
                recipients="FORGE,BOLT",
                subject=f"❌ SSH Connection Failed: {profile}",
                content=f"Failed to connect to {profile}\n"
                        f"Error: {str(e)}",
                priority="HIGH"
            )
        raise
```

---

### 4. LogHunter Integration

**Purpose:** Track SSH connection logs for troubleshooting.

**Setup:**

```python
from loghunter import LogHunter
from portmanager import CONFIG_DIR

# Monitor PortManager operations
hunter = LogHunter()
hunter.add_source(CONFIG_DIR / 'portmanager.log')

# Search for connection issues
results = hunter.search(
    pattern=r"(connection refused|timeout|permission denied)",
    case_insensitive=True,
    last_hours=24
)

for match in results:
    print(f"Issue at {match.timestamp}: {match.line}")
```

---

### 5. ErrorRecovery Integration

**Purpose:** Automatically recover from SSH connection failures.

**Implementation:**

```python
from errorrecovery import ErrorRecovery, RecoveryStrategy
from portmanager import connect, disconnect

class SSHRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for SSH connection failures."""
    
    def __init__(self, profile: str, max_retries: int = 3):
        self.profile = profile
        self.max_retries = max_retries
    
    def can_handle(self, error: Exception) -> bool:
        return "ssh" in str(error).lower() or "connection" in str(error).lower()
    
    def recover(self, error: Exception) -> bool:
        for attempt in range(self.max_retries):
            try:
                disconnect(self.profile)  # Clean up
                time.sleep(2 ** attempt)  # Exponential backoff
                connect(self.profile, background=True)
                return True
            except Exception:
                continue
        return False

# Register strategy
recovery = ErrorRecovery()
recovery.register(SSHRecoveryStrategy("prod-server"))
```

---

## Environment-Specific Configurations

### Development Environment

```python
# dev_setup.py
from portmanager import add_profile, add_forward

def setup_dev_profiles():
    """Set up development environment SSH profiles."""
    
    # Local development server
    add_profile('dev-server', 'localhost', 'developer', port=2222)
    add_forward('dev-server', 5432, 5432)  # PostgreSQL
    add_forward('dev-server', 6379, 6379)  # Redis
    
    # Docker container access
    add_profile('docker-host', 'docker.local', 'docker')
    add_forward('docker-host', 2375, 2375)  # Docker API
```

### Production Environment

```python
# prod_setup.py
from portmanager import add_profile, add_forward

def setup_prod_profiles():
    """Set up production environment SSH profiles."""
    
    # Bastion host
    add_profile('bastion', 'bastion.company.com', 'ops', 
                key='~/.ssh/prod_bastion')
    
    # Database access through bastion
    add_forward('bastion', 5432, 5432, remote_host='db.internal')
    add_forward('bastion', 5433, 5432, remote_host='db-replica.internal')
    
    # Monitoring services
    add_forward('bastion', 3000, 3000, remote_host='grafana.internal')
    add_forward('bastion', 9090, 9090, remote_host='prometheus.internal')
```

---

## Security Considerations

### 1. Key Management

```python
# Use ConfigManager for secure key path storage
from configmanager import ConfigManager

config = ConfigManager('ssh-security')
config.load()

# Get key path from secure config
key_path = config.get('ssh.keys.prod_bastion')
add_profile('bastion', 'bastion.com', 'ops', key=key_path)
```

### 2. Profile Encryption

```python
from securevault import SecureVault
from portmanager import save_profiles, load_profiles

vault = SecureVault()

def save_encrypted_profiles():
    """Save profiles with encryption."""
    profiles = load_profiles()
    encrypted = vault.encrypt(json.dumps(profiles))
    # Store encrypted profiles
    vault.save('portmanager_profiles', encrypted)
```

### 3. Audit Logging

```python
import logging
from functools import wraps

logger = logging.getLogger('portmanager.audit')

def audit_connection(func):
    """Log all connection attempts."""
    @wraps(func)
    def wrapper(profile, *args, **kwargs):
        logger.info(f"Connection attempt: {profile} by {os.getenv('USER')}")
        try:
            result = func(profile, *args, **kwargs)
            logger.info(f"Connection success: {profile}")
            return result
        except Exception as e:
            logger.error(f"Connection failed: {profile} - {e}")
            raise
    return wrapper
```

---

## CLI Integration Scripts

### Bash Helper Functions

```bash
# Add to ~/.bashrc or ~/.zshrc

# Quick connect with notification
pmconnect() {
    local profile="$1"
    echo "Connecting to $profile..."
    python -c "
from portmanager import connect
from synapselink import quick_send
result = connect('$profile', background=True)
if result:
    quick_send('FORGE', 'SSH Connected', 'Profile: $profile')
"
}

# List all profiles
pmlist() {
    python -c "from portmanager import list_profiles; list_profiles()"
}

# Quick database tunnel
pmdb() {
    local env="${1:-dev}"
    python portmanager.py connect "${env}-db" -b
    echo "Database tunnel active. Connect to localhost:5432"
}
```

### PowerShell Helper Functions

```powershell
# Add to $PROFILE

function pmconnect {
    param([string]$profile)
    
    Write-Host "Connecting to $profile..." -ForegroundColor Cyan
    python -c @"
from portmanager import connect
connect('$profile', background=True)
print('Connected!')
"@
}

function pmlist {
    python -c "from portmanager import list_profiles; list_profiles()"
}
```

---

## Monitoring and Observability

### Connection Health Checks

```python
from portmanager import load_profiles, load_active
import subprocess

def check_connection_health() -> dict:
    """Check health of all active connections."""
    active = load_active()
    health = {}
    
    for name, conn in active.items():
        profile = conn['profile']
        try:
            # Simple SSH connectivity check
            result = subprocess.run(
                ['ssh', '-q', '-o', 'ConnectTimeout=5', 
                 f"{profile['user']}@{profile['host']}", 'echo ok'],
                capture_output=True, timeout=10
            )
            health[name] = {
                'status': 'healthy' if result.returncode == 0 else 'unhealthy',
                'latency_ms': calculate_latency(profile)
            }
        except subprocess.TimeoutExpired:
            health[name] = {'status': 'timeout'}
        except Exception as e:
            health[name] = {'status': 'error', 'message': str(e)}
    
    return health
```

---

## Deployment Checklist

### Pre-Integration
- [ ] PortManager installed and tested
- [ ] SSH keys configured for all environments
- [ ] Profiles created for dev/staging/prod

### Integration Setup
- [ ] ConfigManager integration configured
- [ ] SynapseLink notifications enabled
- [ ] ErrorRecovery strategies registered
- [ ] Logging configured

### Post-Integration
- [ ] Test all connection profiles
- [ ] Verify forward functionality
- [ ] Confirm notifications working
- [ ] Document team-specific profiles

---

## Troubleshooting Integration

### Issue: ConfigManager sync fails

```python
# Check ConfigManager path
from configmanager import ConfigManager
config = ConfigManager('ssh-profiles')
print(f"Config location: {config.config_path}")
```

### Issue: SynapseLink notifications not sending

```python
# Verify SynapseLink setup
from synapselink import SynapseLink
sl = SynapseLink()
print(f"Synapse active: {sl.synapse_dir.exists()}")
```

### Issue: Profiles not persisting

```python
# Check PortManager config directory
from portmanager import CONFIG_DIR, PROFILES_FILE
print(f"Config dir: {CONFIG_DIR}")
print(f"Exists: {CONFIG_DIR.exists()}")
print(f"Profiles file: {PROFILES_FILE.exists()}")
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-28 | Initial integration plan |

---

**Built by:** FORGE (Team Brain Orchestrator)  
**For:** Logan Smith / Metaphy LLC  
**Workspace:** BEACON_HQ  
