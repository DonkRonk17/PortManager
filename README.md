# 🔌 PortManager

**Smart SSH Connection & Port Forwarding Manager**

Save and manage SSH connections with port forwards. Never type long SSH commands again!

## ✨ Features

- 💾 **Save SSH Profiles** - Store connection details (host, user, port, key)
- 🚀 **Quick Connect** - Connect with a simple name instead of typing full SSH commands
- 📡 **Port Forwarding** - Manage local and remote port forwards
- 🔐 **SSH Key Support** - Use SSH keys for authentication
- 📋 **Profile Management** - List, update, and delete profiles
- 🔌 **Active Tracking** - Monitor active background connections
- ✅ **Zero Dependencies** - Pure Python, works everywhere

## 🚀 Quick Start

### Installation

```bash
# Clone or download
git clone https://github.com/DonkRonk17/PortManager.git
cd PortManager

# Make executable (Unix/Mac)
chmod +x portmanager.py

# Run
python portmanager.py --help
```

### Basic Usage

```bash
# Add an SSH profile
python portmanager.py add myserver user@example.com

# Add profile with SSH key
python portmanager.py add myserver user@example.com --key ~/.ssh/id_rsa --port 2222

# Add port forward to profile
python portmanager.py forward myserver 8080 80

# Connect using profile
python portmanager.py connect myserver

# List all profiles
python portmanager.py list
```

## 📖 Complete Guide

### 1. Adding SSH Profiles

```bash
# Basic profile
python portmanager.py add myserver user@example.com

# With custom port
python portmanager.py add myserver user@example.com --port 2222

# With SSH key
python portmanager.py add myserver user@example.com --key ~/.ssh/id_rsa

# All options
python portmanager.py add myserver user@example.com --port 2222 --key ~/.ssh/my_key
```

### 2. Managing Port Forwards

**Local Port Forward** (Access remote service locally):
```bash
# Forward local:8080 to remote:80
python portmanager.py forward myserver 8080 80

# Forward to specific remote host
python portmanager.py forward myserver 3306 3306 --host db.internal
```

**Remote Port Forward** (Expose local service remotely):
```bash
# Expose local:3000 on remote:3000
python portmanager.py forward myserver 3000 3000 --remote
```

**Common Use Cases:**
```bash
# Access remote database locally
python portmanager.py forward prod-db 5432 5432

# Access remote web server
python portmanager.py forward web-server 8080 80

# Access internal service through bastion
python portmanager.py forward bastion 9200 9200 --host elasticsearch.internal
```

### 3. Connecting to Servers

**Interactive Connection:**
```bash
python portmanager.py connect myserver
```

**Background Connection (with port forwards):**
```bash
python portmanager.py connect myserver --background
```

### 4. Managing Profiles

**List All Profiles:**
```bash
python portmanager.py list
```

Output example:
```
📋 Saved Profiles (3):

  prod-db
    Connection: admin@db.example.com:22
    Auth: Key: ~/.ssh/prod_key
    Forwards:
      L: localhost:5432 → localhost:5432
    Last used: 2026-01-15 10:30

  web-server
    Connection: deploy@web.example.com:2222
    Auth: Password
    Last used: never
```

**Delete a Profile:**
```bash
python portmanager.py delete myserver
```

### 5. Active Connections

**Show Active Background Connections:**
```bash
python portmanager.py active
```

## 🎯 Real-World Examples

### Example 1: Database Access

```bash
# Save production database profile
python portmanager.py add prod-db admin@db.production.com --key ~/.ssh/prod_key

# Add port forward
python portmanager.py forward prod-db 5432 5432

# Connect (now you can access postgres at localhost:5432)
python portmanager.py connect prod-db --background

# Use with psql
psql -h localhost -p 5432 -U admin mydb
```

### Example 2: Multi-Service Access

```bash
# Save bastion host
python portmanager.py add bastion ops@bastion.company.com --key ~/.ssh/company_key

# Forward multiple internal services
python portmanager.py forward bastion 9200 9200 --host elasticsearch.internal
python portmanager.py forward bastion 5601 5601 --host kibana.internal
python portmanager.py forward bastion 3000 3000 --host grafana.internal

# Connect once, access all services
python portmanager.py connect bastion --background

# Now access:
# - Elasticsearch: http://localhost:9200
# - Kibana: http://localhost:5601
# - Grafana: http://localhost:3000
```

### Example 3: Development Server

```bash
# Save dev server
python portmanager.py add dev-server yourname@dev.company.com

# Forward common dev ports
python portmanager.py forward dev-server 3000 3000  # React/Node
python portmanager.py forward dev-server 8080 8080  # Backend API
python portmanager.py forward dev-server 5432 5432  # PostgreSQL

# Quick connect
python portmanager.py connect dev-server
```

## 📁 Configuration

PortManager stores profiles in:
- **Windows:** `C:\Users\<username>\.portmanager\`
- **Mac/Linux:** `~/.portmanager/`

Files:
- `profiles.json` - Saved SSH profiles
- `active_connections.json` - Active background connections

## 🔒 Security Notes

- SSH keys are referenced, not stored
- Passwords are not stored (use SSH keys!)
- Profiles stored in plain JSON (chmod 600 recommended)
- Always use SSH keys for production systems

## 🌐 Cross-Platform

Works on:
- ✅ **Windows** (via OpenSSH or PuTTY)
- ✅ **macOS** (built-in SSH)
- ✅ **Linux** (all distributions)

**Requirements:**
- Python 3.6+
- SSH client installed (`ssh` command available)

## 🛠️ Troubleshooting

### "Profile not found"
```bash
# List all profiles to see available names
python portmanager.py list
```

### "Permission denied (publickey)"
```bash
# Make sure SSH key is added to ssh-agent
ssh-add ~/.ssh/your_key

# Or specify key explicitly when adding profile
python portmanager.py add myserver user@host --key ~/.ssh/your_key
```

### "Port already in use"
```bash
# Check if port forward is already active
python portmanager.py active

# Or check system processes
netstat -an | grep <port>
```

### Connection hangs
```bash
# Test SSH connection manually first
ssh -v user@host

# Check if host is reachable
ping host
```

## 💡 Tips & Tricks

### Bash Aliases (Unix/Mac)
```bash
# Add to ~/.bashrc or ~/.zshrc
alias pm='python /path/to/portmanager.py'
alias pmc='python /path/to/portmanager.py connect'
alias pml='python /path/to/portmanager.py list'

# Now use:
pm list
pmc myserver
```

### PowerShell Aliases (Windows)
```powershell
# Add to $PROFILE
function pm { python C:\path\to\portmanager.py $args }
function pmc { python C:\path\to\portmanager.py connect $args }

# Now use:
pm list
pmc myserver
```

### Quick Profile Templates
```bash
# Web server with standard ports
python portmanager.py add web user@host --port 22
python portmanager.py forward web 80 80
python portmanager.py forward web 443 443

# Database server
python portmanager.py add db user@host --key ~/.ssh/db_key
python portmanager.py forward db 5432 5432  # PostgreSQL
python portmanager.py forward db 3306 3306  # MySQL
python portmanager.py forward db 27017 27017  # MongoDB
```

## 📊 Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `add` | Add/update SSH profile | `pm add name user@host` |
| `list` | List all profiles | `pm list` |
| `delete` | Delete a profile | `pm delete name` |
| `forward` | Add port forward | `pm forward name 8080 80` |
| `connect` | Connect to server | `pm connect name` |
| `active` | Show active connections | `pm active` |

### Add Options
- `--port PORT` - SSH port (default: 22)
- `--key PATH` - Path to SSH private key

### Forward Options
- `--host HOST` - Remote host (default: localhost)
- `--remote` - Remote forward instead of local

### Connect Options
- `--background` / `-b` - Run in background

## 🤝 Contributing

Issues and pull requests welcome! This project is part of the AutoProjects suite.

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Related Projects

Part of the **AutoProjects** suite:
- [RestCLI](https://github.com/DonkRonk17/RestCLI) - REST API testing
- [NetScan](https://github.com/DonkRonk17/NetScan) - Network utilities
- [LogHunter](https://github.com/DonkRonk17/LogHunter) - Log analysis

---

**Created by:** Holy Grail Automation  
**Version:** 1.0.0  
**Zero Dependencies** | **Cross-Platform** | **Open Source**
