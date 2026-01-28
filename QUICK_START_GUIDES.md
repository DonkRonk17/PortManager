# PortManager Quick Start Guides

> Get started in under 5 minutes

---

## Table of Contents

1. [30-Second Quick Start](#30-second-quick-start)
2. [Developer Quick Start](#developer-quick-start)
3. [DevOps Quick Start](#devops-quick-start)
4. [Team Brain Integration Quick Start](#team-brain-integration-quick-start)
5. [Python API Quick Start](#python-api-quick-start)

---

## 30-Second Quick Start

The absolute minimum to get going:

```bash
# 1. Add a server
python portmanager.py add myserver user@hostname.com

# 2. Connect to it
python portmanager.py connect myserver

# Done! You're connected.
```

---

## Developer Quick Start

**Time:** 3 minutes  
**Goal:** Set up SSH tunnels for your development environment

### Step 1: Add Your Development Server

```bash
python portmanager.py add dev-server yourname@dev.company.com
```

### Step 2: Add Port Forwards for Your Stack

```bash
# Database (PostgreSQL)
python portmanager.py forward dev-server 5432 5432

# Backend API
python portmanager.py forward dev-server 8000 8000

# Frontend dev server
python portmanager.py forward dev-server 3000 3000
```

### Step 3: Connect

```bash
# Background mode - keeps tunnel open, returns to prompt
python portmanager.py connect dev-server --background
```

### Step 4: Access Your Services

- Database: `localhost:5432`
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

### Verify It Works

```bash
# Check active connections
python portmanager.py active

# Test database connection
psql -h localhost -p 5432 -U yourname mydb
```

---

## DevOps Quick Start

**Time:** 5 minutes  
**Goal:** Set up bastion access to multiple internal services

### Step 1: Create Bastion Profile with SSH Key

```bash
python portmanager.py add bastion ops@bastion.company.com --key ~/.ssh/bastion_key
```

### Step 2: Add Forwards to Internal Services

```bash
# Database cluster
python portmanager.py forward bastion 5432 5432 --host postgres.internal
python portmanager.py forward bastion 5433 5432 --host postgres-replica.internal

# Monitoring
python portmanager.py forward bastion 3000 3000 --host grafana.internal
python portmanager.py forward bastion 9090 9090 --host prometheus.internal
python portmanager.py forward bastion 9200 9200 --host elasticsearch.internal
python portmanager.py forward bastion 5601 5601 --host kibana.internal

# Cache
python portmanager.py forward bastion 6379 6379 --host redis.internal
```

### Step 3: Verify Configuration

```bash
python portmanager.py list
```

**Expected output:**
```
[*] Saved Profiles (1):

  bastion
    Connection: ops@bastion.company.com:22
    Auth: Key: ~/.ssh/bastion_key
    Forwards:
      L: localhost:5432 -> postgres.internal:5432
      L: localhost:5433 -> postgres-replica.internal:5432
      L: localhost:3000 -> grafana.internal:3000
      L: localhost:9090 -> prometheus.internal:9090
      L: localhost:9200 -> elasticsearch.internal:9200
      L: localhost:5601 -> kibana.internal:5601
      L: localhost:6379 -> redis.internal:6379
```

### Step 4: Connect and Access

```bash
# Start tunnel
python portmanager.py connect bastion -b

# Access services
curl http://localhost:3000        # Grafana
curl http://localhost:9200        # Elasticsearch
redis-cli -h localhost -p 6379    # Redis
```

---

## Team Brain Integration Quick Start

**Time:** 5 minutes  
**Goal:** Integrate PortManager with Team Brain ecosystem

### Step 1: Install PortManager

```bash
cd C:\Users\logan\OneDrive\Documents\AutoProjects\PortManager
pip install -e .
```

### Step 2: Set Up BCH Server Profile

```bash
# BCH development server
python portmanager.py add bch-dev logan@bch-dev.beacon-hq.com --key ~/.ssh/bch

# Add forwards for BCH services
python portmanager.py forward bch-dev 8080 8080  # Frontend
python portmanager.py forward bch-dev 5001 5001  # Backend API
python portmanager.py forward bch-dev 5432 5432  # PostgreSQL
```

### Step 3: Create Connection Helper Script

```python
# bch_connect.py
from portmanager import connect, load_profiles
from synapselink import quick_send

def connect_bch(environment='dev'):
    """Connect to BCH server and notify team."""
    profile_name = f'bch-{environment}'
    
    # Verify profile exists
    profiles = load_profiles()
    if profile_name not in profiles:
        print(f"Error: Profile '{profile_name}' not found")
        return False
    
    # Connect
    result = connect(profile_name, background=True)
    
    if result:
        # Notify team
        quick_send(
            recipients="FORGE,BOLT",
            subject=f"BCH Connection: {environment.upper()}",
            content=f"Logan connected to bch-{environment}\n"
                    f"Time: {datetime.now().isoformat()}\n"
                    f"Services available: Frontend, Backend, Database",
            priority="LOW"
        )
    
    return result

if __name__ == "__main__":
    import sys
    env = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    connect_bch(env)
```

### Step 4: Test Integration

```bash
# Connect to BCH
python bch_connect.py dev

# Verify in Synapse
ls D:\BEACON_HQ\MEMORY_CORE_V2\03_INTER_AI_COMMS\THE_SYNAPSE\active\
```

---

## Python API Quick Start

**Time:** 2 minutes  
**Goal:** Use PortManager programmatically

### Basic Usage

```python
from portmanager import (
    add_profile,
    add_forward,
    delete_profile,
    list_profiles,
    connect,
    show_active,
    build_ssh_command,
    load_profiles
)

# 1. Create a profile
add_profile(
    name='my-server',
    host='example.com',
    user='admin',
    port=22,
    key='~/.ssh/id_rsa'
)

# 2. Add port forwards
add_forward('my-server', 8080, 80)
add_forward('my-server', 5432, 5432, remote_host='db.internal')
add_forward('my-server', 3000, 3000, forward_type='remote')

# 3. View configuration
list_profiles()

# 4. Get the SSH command (for debugging or external use)
profiles = load_profiles()
cmd = build_ssh_command(profiles['my-server'])
print("SSH Command:", ' '.join(cmd))

# 5. Connect
connect('my-server', background=True)

# 6. Check active connections
show_active()
```

### Script Template

```python
#!/usr/bin/env python3
"""
My PortManager automation script.
"""

from portmanager import add_profile, add_forward, connect

def setup_environment():
    """Set up my SSH profiles."""
    
    # Production
    add_profile('prod', 'prod.example.com', 'deploy', key='~/.ssh/prod')
    add_forward('prod', 5432, 5432)
    
    # Staging
    add_profile('staging', 'staging.example.com', 'deploy', key='~/.ssh/staging')
    add_forward('staging', 5433, 5432)  # Different local port
    
    print("Profiles configured!")

def connect_to_env(env: str):
    """Connect to an environment."""
    print(f"Connecting to {env}...")
    connect(env, background=True)
    print("Connected!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'setup':
            setup_environment()
        elif cmd == 'connect':
            env = sys.argv[2] if len(sys.argv) > 2 else 'prod'
            connect_to_env(env)
    else:
        print("Usage: script.py [setup|connect] [env]")
```

---

## Next Steps

After completing a quick start guide:

1. **Read the full documentation:** [README.md](README.md)
2. **See more examples:** [EXAMPLES.md](EXAMPLES.md)
3. **Integration details:** [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md)
4. **Quick reference:** [CHEAT_SHEET.txt](CHEAT_SHEET.txt)

---

## Troubleshooting Quick Start Issues

### "Profile not found"

```bash
# List existing profiles
python portmanager.py list

# Profile names are case-sensitive
python portmanager.py add MyServer user@host  # Creates 'MyServer'
python portmanager.py connect myserver         # FAILS - wrong case
python portmanager.py connect MyServer         # Works
```

### "Permission denied (publickey)"

```bash
# Add your SSH key to ssh-agent first
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/your_key

# Or specify the key when creating the profile
python portmanager.py add server user@host --key ~/.ssh/your_key
```

### "Connection refused"

```bash
# Test direct SSH first
ssh -v user@host

# Check if SSH is running on remote
# Check firewall rules
# Verify the port is correct
```

### "Address already in use"

```bash
# Another process is using the local port
# Option 1: Find and kill it
netstat -ano | findstr :5432  # Windows
lsof -i :5432                  # macOS/Linux

# Option 2: Use a different local port
python portmanager.py forward server 5433 5432  # Local 5433 -> Remote 5432
```

---

**Built by:** FORGE (Team Brain)  
**For:** Logan Smith / Metaphy LLC  
**Date:** January 2026
