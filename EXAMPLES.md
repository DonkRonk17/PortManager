# PortManager Examples

> 10 Real-World Examples for Managing SSH Connections and Port Forwards

---

## Table of Contents

1. [Example 1: Basic Profile Creation](#example-1-basic-profile-creation)
2. [Example 2: Production Database Access](#example-2-production-database-access)
3. [Example 3: Multi-Service Bastion Setup](#example-3-multi-service-bastion-setup)
4. [Example 4: Development Server Configuration](#example-4-development-server-configuration)
5. [Example 5: Remote Desktop (VNC) Forwarding](#example-5-remote-desktop-vnc-forwarding)
6. [Example 6: Kubernetes Dashboard Access](#example-6-kubernetes-dashboard-access)
7. [Example 7: Expose Local Service Remotely](#example-7-expose-local-service-remotely)
8. [Example 8: Multiple Environments (Dev/Staging/Prod)](#example-8-multiple-environments-devstagingprod)
9. [Example 9: Jump Host / Bastion Pattern](#example-9-jump-host--bastion-pattern)
10. [Example 10: Complete Workflow Integration](#example-10-complete-workflow-integration)

---

## Example 1: Basic Profile Creation

**Scenario:** You have a web server you frequently access and want to save the connection details.

**Steps:**

```bash
# Create a simple profile
python portmanager.py add webserver admin@webserver.example.com

# Connect to it
python portmanager.py connect webserver
```

**Expected Output:**
```
[OK] Profile 'webserver' saved!
  admin@webserver.example.com:22
```

**What You Learned:**
- How to create a basic SSH profile
- Connection format: `user@host`
- Default port is 22

---

## Example 2: Production Database Access

**Scenario:** You need to access a PostgreSQL database on a remote server that's behind a firewall.

**Steps:**

```bash
# Add production database profile with SSH key
python portmanager.py add prod-db dbadmin@db.production.com --key ~/.ssh/prod_key

# Add PostgreSQL port forward (local:5432 → remote:5432)
python portmanager.py forward prod-db 5432 5432

# Connect in background (keeps tunnel open)
python portmanager.py connect prod-db --background

# Now connect to postgres locally
psql -h localhost -p 5432 -U dbadmin production_db
```

**Expected Output:**
```
[OK] Profile 'prod-db' saved!
  dbadmin@db.production.com:22
  Key: ~/.ssh/prod_key

[OK] Added local forward to 'prod-db': localhost:5432 -> localhost:5432

[*] Connecting to 'prod-db'...
   dbadmin@db.production.com:22

[>] Port Forwards:
   L: localhost:5432 -> localhost:5432

[OK] Connection started in background
```

**What You Learned:**
- Using SSH keys for authentication
- Setting up local port forwards
- Running connections in background for persistent tunnels

---

## Example 3: Multi-Service Bastion Setup

**Scenario:** You have a bastion host that provides access to multiple internal services (Elasticsearch, Kibana, Redis).

**Steps:**

```bash
# Create bastion profile
python portmanager.py add bastion ops@bastion.company.com --key ~/.ssh/company

# Forward Elasticsearch (internal service)
python portmanager.py forward bastion 9200 9200 --host elasticsearch.internal

# Forward Kibana
python portmanager.py forward bastion 5601 5601 --host kibana.internal

# Forward Redis
python portmanager.py forward bastion 6379 6379 --host redis.internal

# Forward Grafana
python portmanager.py forward bastion 3000 3000 --host grafana.internal

# Connect and access all services
python portmanager.py connect bastion --background
```

**Expected Output:**
```
[*] Saved Profiles (1):

  bastion
    Connection: ops@bastion.company.com:22
    Auth: Key: ~/.ssh/company
    Forwards:
      L: localhost:9200 -> elasticsearch.internal:9200
      L: localhost:5601 -> kibana.internal:5601
      L: localhost:6379 -> redis.internal:6379
      L: localhost:3000 -> grafana.internal:3000
    Last used: 2026-01-28 10:30
```

**Now Access Locally:**
- Elasticsearch: `curl http://localhost:9200`
- Kibana: `http://localhost:5601`
- Redis: `redis-cli -h localhost -p 6379`
- Grafana: `http://localhost:3000`

**What You Learned:**
- Forwarding to internal hosts (not localhost on remote)
- Setting up multiple forwards on one profile
- Accessing multiple services through single SSH connection

---

## Example 4: Development Server Configuration

**Scenario:** You have a remote development server with multiple ports for your app stack.

**Steps:**

```bash
# Add development server
python portmanager.py add dev-server yourname@dev.company.com --port 2222

# Forward frontend (React/Vite)
python portmanager.py forward dev-server 3000 3000

# Forward backend (FastAPI/Flask)
python portmanager.py forward dev-server 8000 8000

# Forward database
python portmanager.py forward dev-server 5432 5432

# Forward Redis
python portmanager.py forward dev-server 6379 6379

# View configuration
python portmanager.py list
```

**Expected Output:**
```
[*] Saved Profiles (1):

  dev-server
    Connection: yourname@dev.company.com:2222
    Auth: Password
    Forwards:
      L: localhost:3000 -> localhost:3000
      L: localhost:8000 -> localhost:8000
      L: localhost:5432 -> localhost:5432
      L: localhost:6379 -> localhost:6379
    Last used: never
```

**What You Learned:**
- Using custom SSH ports (not just 22)
- Setting up a complete dev environment tunnel

---

## Example 5: Remote Desktop (VNC) Forwarding

**Scenario:** You need to access a VNC server on a remote machine securely.

**Steps:**

```bash
# Add server with VNC
python portmanager.py add vnc-server admin@workstation.example.com --key ~/.ssh/admin_key

# Forward VNC port (5900 is standard VNC)
python portmanager.py forward vnc-server 5900 5900

# Connect
python portmanager.py connect vnc-server --background

# Now connect VNC client to localhost:5900
```

**Expected Output:**
```
[OK] Added local forward to 'vnc-server': localhost:5900 -> localhost:5900

[*] Connecting to 'vnc-server'...
   admin@workstation.example.com:22

[>] Port Forwards:
   L: localhost:5900 -> localhost:5900
```

**What You Learned:**
- Forwarding graphical desktop protocols securely
- VNC tunneling over SSH

---

## Example 6: Kubernetes Dashboard Access

**Scenario:** Access Kubernetes dashboard running in a cluster through a bastion.

**Steps:**

```bash
# Add k8s bastion
python portmanager.py add k8s-bastion k8sadmin@k8s-bastion.company.com --key ~/.ssh/k8s

# Forward K8s API server
python portmanager.py forward k8s-bastion 6443 6443 --host kubernetes.default.svc.cluster.local

# Forward dashboard
python portmanager.py forward k8s-bastion 8001 8001 --host kubernetes-dashboard.kubernetes-dashboard.svc.cluster.local

# Connect
python portmanager.py connect k8s-bastion --background

# Access dashboard
# https://localhost:8001
```

**What You Learned:**
- Forwarding to Kubernetes internal DNS names
- Secure access to cluster services

---

## Example 7: Expose Local Service Remotely

**Scenario:** You want to expose a local web app (running on your machine) to a remote server for testing.

**Steps:**

```bash
# Add remote server
python portmanager.py add demo-server user@demo.example.com

# Add REMOTE forward - exposes local:3000 on remote:8080
python portmanager.py forward demo-server 3000 8080 --remote

# Connect
python portmanager.py connect demo-server --background

# Now remote server can access your local app at localhost:8080
```

**Expected Output:**
```
[OK] Added remote forward to 'demo-server': localhost:8080 -> localhost:3000

[*] Connecting to 'demo-server'...
   user@demo.example.com:22

[>] Port Forwards:
   R: localhost:8080 -> localhost:3000
```

**What You Learned:**
- Remote port forwards (reverse tunnels)
- Exposing local services to remote machines
- Difference between -L (local) and -R (remote) forwards

---

## Example 8: Multiple Environments (Dev/Staging/Prod)

**Scenario:** Set up profiles for all your environments.

**Steps:**

```bash
# Development
python portmanager.py add dev dev@dev.example.com --key ~/.ssh/dev
python portmanager.py forward dev 5432 5432

# Staging
python portmanager.py add staging deploy@staging.example.com --key ~/.ssh/staging
python portmanager.py forward staging 5432 5433  # Different local port!

# Production
python portmanager.py add prod deploy@prod.example.com --key ~/.ssh/prod
python portmanager.py forward prod 5432 5434  # Different local port!

# List all
python portmanager.py list

# Connect to any environment quickly
python portmanager.py connect dev
python portmanager.py connect staging
python portmanager.py connect prod
```

**Expected Output:**
```
[*] Saved Profiles (3):

  dev
    Connection: dev@dev.example.com:22
    Auth: Key: ~/.ssh/dev
    Forwards:
      L: localhost:5432 -> localhost:5432
    Last used: 2026-01-28 09:00

  prod
    Connection: deploy@prod.example.com:22
    Auth: Key: ~/.ssh/prod
    Forwards:
      L: localhost:5434 -> localhost:5432
    Last used: never

  staging
    Connection: deploy@staging.example.com:22
    Auth: Key: ~/.ssh/staging
    Forwards:
      L: localhost:5433 -> localhost:5432
    Last used: 2026-01-28 11:00
```

**What You Learned:**
- Managing multiple environments
- Using different local ports to avoid conflicts
- Quick switching between environments

---

## Example 9: Jump Host / Bastion Pattern

**Scenario:** You need to access a server that's only reachable through a jump host.

**Steps:**

```bash
# First, set up the jump host profile
python portmanager.py add jump-host admin@jump.example.com --key ~/.ssh/jump

# Forward SSH port of the final destination through jump host
python portmanager.py forward jump-host 2222 22 --host internal-server.private

# Connect to jump host (establishes tunnel)
python portmanager.py connect jump-host --background

# Now you can SSH to internal server through localhost:2222
ssh -p 2222 user@localhost
```

**What You Learned:**
- SSH jump host patterns
- Chaining SSH connections
- Accessing double-NAT'd servers

---

## Example 10: Complete Workflow Integration

**Scenario:** Full Team Brain workflow - set up tunnels, check status, manage connections.

**Steps:**

```bash
# 1. Create all needed profiles
python portmanager.py add bch-server logan@bch.beacon-hq.com --key ~/.ssh/bch
python portmanager.py forward bch-server 8080 8080  # BCH Frontend
python portmanager.py forward bch-server 5001 5001  # BCH Backend
python portmanager.py forward bch-server 5432 5432  # PostgreSQL

# 2. List to verify configuration
python portmanager.py list

# 3. Start connection in background
python portmanager.py connect bch-server --background

# 4. Check active connections
python portmanager.py active

# 5. Later, when done, simply close the terminal or kill the SSH process
```

**Python API Usage:**

```python
from portmanager import add_profile, add_forward, connect, list_profiles

# Create profile programmatically
add_profile('api-server', 'api.example.com', 'deploy', key='~/.ssh/deploy_key')

# Add forwards
add_forward('api-server', 8000, 8000)
add_forward('api-server', 5432, 5432)

# Connect in background
connect('api-server', background=True)
```

**What You Learned:**
- Complete workflow from setup to teardown
- Combining all PortManager features
- Integration with Team Brain tools

---

## Quick Reference

| Task | Command |
|------|---------|
| Add basic profile | `portmanager add NAME user@host` |
| Add with key | `portmanager add NAME user@host --key ~/.ssh/key` |
| Add with port | `portmanager add NAME user@host --port 2222` |
| Add local forward | `portmanager forward NAME 8080 80` |
| Add forward to internal host | `portmanager forward NAME 8080 80 --host internal.server` |
| Add remote forward | `portmanager forward NAME 3000 3000 --remote` |
| Connect interactively | `portmanager connect NAME` |
| Connect in background | `portmanager connect NAME -b` |
| List profiles | `portmanager list` |
| Show active | `portmanager active` |
| Delete profile | `portmanager delete NAME` |

---

## Next Steps

- See [CHEAT_SHEET.txt](CHEAT_SHEET.txt) for quick reference
- See [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) for Team Brain integration
- See [README.md](README.md) for complete documentation

---

**Built by:** FORGE (Team Brain)  
**For:** Logan Smith / Metaphy LLC  
**Date:** January 2026
