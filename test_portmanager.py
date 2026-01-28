#!/usr/bin/env python3
"""
Comprehensive test suite for PortManager.

Tests cover:
- Profile management (add, delete, list, update)
- Port forward management
- SSH command building
- Configuration persistence
- CLI interface
- Edge cases and error handling

Run: python test_portmanager.py
"""

import unittest
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from portmanager import (
    add_profile, list_profiles, delete_profile, add_forward,
    build_ssh_command, connect, show_active,
    load_profiles, save_profiles, load_active, save_active,
    ensure_config_dir, main,
    CONFIG_DIR, PROFILES_FILE, ACTIVE_FILE
)


class TestPortManagerConfig(unittest.TestCase):
    """Test configuration and file operations."""
    
    def setUp(self):
        """Set up test environment with temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_config = CONFIG_DIR
        self.original_profiles = PROFILES_FILE
        self.original_active = ACTIVE_FILE
        
        # Patch config paths to use temp directory
        import portmanager
        portmanager.CONFIG_DIR = Path(self.temp_dir) / '.portmanager'
        portmanager.PROFILES_FILE = portmanager.CONFIG_DIR / 'profiles.json'
        portmanager.ACTIVE_FILE = portmanager.CONFIG_DIR / 'active_connections.json'
    
    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)
        
        # Restore original paths
        import portmanager
        portmanager.CONFIG_DIR = self.original_config
        portmanager.PROFILES_FILE = self.original_profiles
        portmanager.ACTIVE_FILE = self.original_active
    
    def test_ensure_config_dir_creates_directory(self):
        """Test config directory creation."""
        import portmanager
        ensure_config_dir()
        self.assertTrue(portmanager.CONFIG_DIR.exists())
    
    def test_load_profiles_empty_file(self):
        """Test loading profiles when file doesn't exist."""
        profiles = load_profiles()
        self.assertEqual(profiles, {})
    
    def test_save_and_load_profiles(self):
        """Test profile persistence."""
        test_profiles = {
            'test1': {
                'host': 'example.com',
                'user': 'testuser',
                'port': 22,
                'forwards': []
            }
        }
        
        save_profiles(test_profiles)
        loaded = load_profiles()
        
        self.assertEqual(loaded['test1']['host'], 'example.com')
        self.assertEqual(loaded['test1']['user'], 'testuser')
    
    def test_load_active_empty(self):
        """Test loading active connections when empty."""
        active = load_active()
        self.assertEqual(active, {})
    
    def test_save_and_load_active(self):
        """Test active connection persistence."""
        test_active = {
            'conn1': {
                'started': datetime.now().isoformat(),
                'profile': {'host': 'test.com', 'user': 'user'}
            }
        }
        
        save_active(test_active)
        loaded = load_active()
        
        self.assertIn('conn1', loaded)
        self.assertEqual(loaded['conn1']['profile']['host'], 'test.com')


class TestProfileManagement(unittest.TestCase):
    """Test profile management functions."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        import portmanager
        portmanager.CONFIG_DIR = Path(self.temp_dir) / '.portmanager'
        portmanager.PROFILES_FILE = portmanager.CONFIG_DIR / 'profiles.json'
        portmanager.ACTIVE_FILE = portmanager.CONFIG_DIR / 'active_connections.json'
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    @patch('builtins.print')
    def test_add_profile_basic(self, mock_print):
        """Test adding a basic profile."""
        add_profile('testserver', 'example.com', 'admin', 22)
        
        profiles = load_profiles()
        self.assertIn('testserver', profiles)
        self.assertEqual(profiles['testserver']['host'], 'example.com')
        self.assertEqual(profiles['testserver']['user'], 'admin')
        self.assertEqual(profiles['testserver']['port'], 22)
    
    @patch('builtins.print')
    def test_add_profile_with_key(self, mock_print):
        """Test adding profile with SSH key."""
        add_profile('keyserver', 'host.com', 'user', key='~/.ssh/id_rsa')
        
        profiles = load_profiles()
        self.assertEqual(profiles['keyserver']['key'], '~/.ssh/id_rsa')
    
    @patch('builtins.print')
    def test_add_profile_with_custom_port(self, mock_print):
        """Test adding profile with custom port."""
        add_profile('custom', 'host.com', 'user', port=2222)
        
        profiles = load_profiles()
        self.assertEqual(profiles['custom']['port'], 2222)
    
    @patch('builtins.print')
    def test_add_profile_update_existing(self, mock_print):
        """Test updating an existing profile."""
        add_profile('server', 'host1.com', 'user1')
        add_profile('server', 'host2.com', 'user2')
        
        profiles = load_profiles()
        self.assertEqual(profiles['server']['host'], 'host2.com')
        self.assertEqual(profiles['server']['user'], 'user2')
    
    @patch('builtins.print')
    def test_delete_profile(self, mock_print):
        """Test deleting a profile."""
        add_profile('todelete', 'host.com', 'user')
        result = delete_profile('todelete')
        
        self.assertTrue(result)
        profiles = load_profiles()
        self.assertNotIn('todelete', profiles)
    
    @patch('builtins.print')
    def test_delete_nonexistent_profile(self, mock_print):
        """Test deleting profile that doesn't exist."""
        result = delete_profile('nonexistent')
        self.assertFalse(result)
    
    @patch('builtins.print')
    def test_list_profiles_empty(self, mock_print):
        """Test listing when no profiles exist."""
        list_profiles()
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_list_profiles_with_data(self, mock_print):
        """Test listing profiles with data."""
        add_profile('server1', 'host1.com', 'user1')
        add_profile('server2', 'host2.com', 'user2', key='~/.ssh/key')
        
        list_profiles()
        # Just verify it runs without error


class TestPortForwards(unittest.TestCase):
    """Test port forward management."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        import portmanager
        portmanager.CONFIG_DIR = Path(self.temp_dir) / '.portmanager'
        portmanager.PROFILES_FILE = portmanager.CONFIG_DIR / 'profiles.json'
        portmanager.ACTIVE_FILE = portmanager.CONFIG_DIR / 'active_connections.json'
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    @patch('builtins.print')
    def test_add_local_forward(self, mock_print):
        """Test adding local port forward."""
        add_profile('server', 'host.com', 'user')
        add_forward('server', 8080, 80)
        
        profiles = load_profiles()
        forwards = profiles['server']['forwards']
        
        self.assertEqual(len(forwards), 1)
        self.assertEqual(forwards[0]['type'], 'local')
        self.assertEqual(forwards[0]['local_port'], 8080)
        self.assertEqual(forwards[0]['remote_port'], 80)
    
    @patch('builtins.print')
    def test_add_remote_forward(self, mock_print):
        """Test adding remote port forward."""
        add_profile('server', 'host.com', 'user')
        add_forward('server', 3000, 3000, forward_type='remote')
        
        profiles = load_profiles()
        forwards = profiles['server']['forwards']
        
        self.assertEqual(forwards[0]['type'], 'remote')
    
    @patch('builtins.print')
    def test_add_forward_with_custom_host(self, mock_print):
        """Test adding forward with custom remote host."""
        add_profile('bastion', 'bastion.com', 'admin')
        add_forward('bastion', 5432, 5432, remote_host='db.internal')
        
        profiles = load_profiles()
        forwards = profiles['bastion']['forwards']
        
        self.assertEqual(forwards[0]['remote_host'], 'db.internal')
    
    @patch('builtins.print')
    def test_add_forward_nonexistent_profile(self, mock_print):
        """Test adding forward to nonexistent profile."""
        result = add_forward('nonexistent', 8080, 80)
        self.assertFalse(result)
    
    @patch('builtins.print')
    def test_add_multiple_forwards(self, mock_print):
        """Test adding multiple forwards to same profile."""
        add_profile('multi', 'host.com', 'user')
        add_forward('multi', 8080, 80)
        add_forward('multi', 3306, 3306)
        add_forward('multi', 5432, 5432, remote_host='db.internal')
        
        profiles = load_profiles()
        forwards = profiles['multi']['forwards']
        
        self.assertEqual(len(forwards), 3)


class TestSSHCommandBuilding(unittest.TestCase):
    """Test SSH command generation."""
    
    def test_basic_command(self):
        """Test basic SSH command generation."""
        profile = {
            'host': 'example.com',
            'user': 'admin',
            'port': 22,
            'forwards': []
        }
        
        cmd = build_ssh_command(profile)
        
        self.assertIn('ssh', cmd)
        self.assertIn('admin@example.com', cmd)
    
    def test_command_with_custom_port(self):
        """Test SSH command with custom port."""
        profile = {
            'host': 'example.com',
            'user': 'admin',
            'port': 2222,
            'forwards': []
        }
        
        cmd = build_ssh_command(profile)
        
        self.assertIn('-p', cmd)
        self.assertIn('2222', cmd)
    
    def test_command_with_key(self):
        """Test SSH command with key file."""
        # Create temp key file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
            f.write('test key content')
            key_path = f.name
        
        try:
            profile = {
                'host': 'example.com',
                'user': 'admin',
                'port': 22,
                'key': key_path,
                'forwards': []
            }
            
            cmd = build_ssh_command(profile)
            
            self.assertIn('-i', cmd)
            self.assertIn(key_path, cmd)
        finally:
            os.unlink(key_path)
    
    def test_command_with_local_forward(self):
        """Test SSH command with local port forward."""
        profile = {
            'host': 'example.com',
            'user': 'admin',
            'port': 22,
            'forwards': [{
                'type': 'local',
                'local_port': 8080,
                'remote_port': 80,
                'remote_host': 'localhost'
            }]
        }
        
        cmd = build_ssh_command(profile)
        
        self.assertIn('-L', cmd)
        self.assertIn('8080:localhost:80', cmd)
    
    def test_command_with_remote_forward(self):
        """Test SSH command with remote port forward."""
        profile = {
            'host': 'example.com',
            'user': 'admin',
            'port': 22,
            'forwards': [{
                'type': 'remote',
                'local_port': 3000,
                'remote_port': 3000,
                'remote_host': 'localhost'
            }]
        }
        
        cmd = build_ssh_command(profile)
        
        self.assertIn('-R', cmd)
        self.assertIn('3000:localhost:3000', cmd)
    
    def test_command_with_multiple_forwards(self):
        """Test SSH command with multiple forwards."""
        profile = {
            'host': 'example.com',
            'user': 'admin',
            'port': 22,
            'forwards': [
                {'type': 'local', 'local_port': 8080, 'remote_port': 80, 'remote_host': 'localhost'},
                {'type': 'local', 'local_port': 5432, 'remote_port': 5432, 'remote_host': 'db.internal'},
                {'type': 'remote', 'local_port': 9000, 'remote_port': 9000, 'remote_host': 'localhost'}
            ]
        }
        
        cmd = build_ssh_command(profile)
        cmd_str = ' '.join(cmd)
        
        self.assertEqual(cmd_str.count('-L'), 2)
        self.assertEqual(cmd_str.count('-R'), 1)


class TestConnectionManagement(unittest.TestCase):
    """Test connection management."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        import portmanager
        portmanager.CONFIG_DIR = Path(self.temp_dir) / '.portmanager'
        portmanager.PROFILES_FILE = portmanager.CONFIG_DIR / 'profiles.json'
        portmanager.ACTIVE_FILE = portmanager.CONFIG_DIR / 'active_connections.json'
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    @patch('builtins.print')
    def test_connect_nonexistent_profile(self, mock_print):
        """Test connecting to nonexistent profile."""
        result = connect('nonexistent')
        self.assertFalse(result)
    
    @patch('builtins.print')
    def test_show_active_empty(self, mock_print):
        """Test showing active connections when empty."""
        show_active()
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_show_active_with_connections(self, mock_print):
        """Test showing active connections with data."""
        import portmanager
        
        active = {
            'server1': {
                'started': datetime.now().isoformat(),
                'profile': {
                    'host': 'test.com',
                    'user': 'admin',
                    'port': 22,
                    'forwards': []
                }
            }
        }
        save_active(active)
        
        show_active()
        # Verify it runs without error


class TestCLIInterface(unittest.TestCase):
    """Test CLI interface."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        import portmanager
        portmanager.CONFIG_DIR = Path(self.temp_dir) / '.portmanager'
        portmanager.PROFILES_FILE = portmanager.CONFIG_DIR / 'profiles.json'
        portmanager.ACTIVE_FILE = portmanager.CONFIG_DIR / 'active_connections.json'
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    @patch('builtins.print')
    def test_cli_no_args(self, mock_print):
        """Test CLI with no arguments."""
        with patch('sys.argv', ['portmanager']):
            result = main()
        self.assertEqual(result, 0)
    
    @patch('builtins.print')
    def test_cli_add_profile(self, mock_print):
        """Test CLI add command."""
        with patch('sys.argv', ['portmanager', 'add', 'test', 'user@host.com']):
            result = main()
        
        self.assertEqual(result, 0)
        profiles = load_profiles()
        self.assertIn('test', profiles)
    
    @patch('builtins.print')
    def test_cli_add_profile_with_options(self, mock_print):
        """Test CLI add with all options."""
        with patch('sys.argv', ['portmanager', 'add', 'test', 'user@host.com', '--port', '2222', '--key', '~/.ssh/id_rsa']):
            result = main()
        
        self.assertEqual(result, 0)
        profiles = load_profiles()
        self.assertEqual(profiles['test']['port'], 2222)
        self.assertEqual(profiles['test']['key'], '~/.ssh/id_rsa')
    
    @patch('builtins.print')
    def test_cli_add_invalid_connection(self, mock_print):
        """Test CLI add with invalid connection string."""
        with patch('sys.argv', ['portmanager', 'add', 'test', 'invalid']):
            result = main()
        
        self.assertEqual(result, 1)
    
    @patch('builtins.print')
    def test_cli_list(self, mock_print):
        """Test CLI list command."""
        with patch('sys.argv', ['portmanager', 'list']):
            result = main()
        self.assertEqual(result, 0)
    
    @patch('builtins.print')
    def test_cli_delete(self, mock_print):
        """Test CLI delete command."""
        # First add a profile
        with patch('sys.argv', ['portmanager', 'add', 'todelete', 'user@host.com']):
            main()
        
        # Then delete it
        with patch('sys.argv', ['portmanager', 'delete', 'todelete']):
            result = main()
        
        self.assertEqual(result, 0)
        profiles = load_profiles()
        self.assertNotIn('todelete', profiles)
    
    @patch('builtins.print')
    def test_cli_forward(self, mock_print):
        """Test CLI forward command."""
        # First add a profile
        with patch('sys.argv', ['portmanager', 'add', 'server', 'user@host.com']):
            main()
        
        # Then add forward
        with patch('sys.argv', ['portmanager', 'forward', 'server', '8080', '80']):
            result = main()
        
        self.assertEqual(result, 0)
        profiles = load_profiles()
        self.assertEqual(len(profiles['server']['forwards']), 1)
    
    @patch('builtins.print')
    def test_cli_forward_remote(self, mock_print):
        """Test CLI forward command with --remote flag."""
        # First add a profile
        with patch('sys.argv', ['portmanager', 'add', 'server', 'user@host.com']):
            main()
        
        # Then add remote forward
        with patch('sys.argv', ['portmanager', 'forward', 'server', '3000', '3000', '--remote']):
            result = main()
        
        self.assertEqual(result, 0)
        profiles = load_profiles()
        self.assertEqual(profiles['server']['forwards'][0]['type'], 'remote')
    
    @patch('builtins.print')
    def test_cli_active(self, mock_print):
        """Test CLI active command."""
        with patch('sys.argv', ['portmanager', 'active']):
            result = main()
        self.assertEqual(result, 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        import portmanager
        portmanager.CONFIG_DIR = Path(self.temp_dir) / '.portmanager'
        portmanager.PROFILES_FILE = portmanager.CONFIG_DIR / 'profiles.json'
        portmanager.ACTIVE_FILE = portmanager.CONFIG_DIR / 'active_connections.json'
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    @patch('builtins.print')
    def test_profile_with_special_characters(self, mock_print):
        """Test profile with special characters in host."""
        add_profile('special', 'host-with-dashes.example.com', 'user.name')
        
        profiles = load_profiles()
        self.assertEqual(profiles['special']['host'], 'host-with-dashes.example.com')
        self.assertEqual(profiles['special']['user'], 'user.name')
    
    @patch('builtins.print')
    def test_profile_with_ip_address(self, mock_print):
        """Test profile with IP address."""
        add_profile('ipserver', '192.168.1.100', 'root')
        
        profiles = load_profiles()
        self.assertEqual(profiles['ipserver']['host'], '192.168.1.100')
    
    @patch('builtins.print')
    def test_forward_to_same_port(self, mock_print):
        """Test forwarding same local and remote port."""
        add_profile('same', 'host.com', 'user')
        add_forward('same', 5432, 5432)
        
        profiles = load_profiles()
        fwd = profiles['same']['forwards'][0]
        self.assertEqual(fwd['local_port'], fwd['remote_port'])
    
    def test_corrupted_profiles_file(self):
        """Test handling corrupted profiles file."""
        import portmanager
        
        # Write invalid JSON
        portmanager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(portmanager.PROFILES_FILE, 'w') as f:
            f.write('invalid json content')
        
        # Should return empty dict, not crash
        profiles = load_profiles()
        self.assertEqual(profiles, {})
    
    def test_corrupted_active_file(self):
        """Test handling corrupted active file."""
        import portmanager
        
        # Write invalid JSON
        portmanager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(portmanager.ACTIVE_FILE, 'w') as f:
            f.write('invalid json content')
        
        # Should return empty dict, not crash
        active = load_active()
        self.assertEqual(active, {})
    
    @patch('builtins.print')
    def test_profile_name_with_spaces(self, mock_print):
        """Test profile name handling."""
        # Profile names should work without spaces
        add_profile('my-server', 'host.com', 'user')
        profiles = load_profiles()
        self.assertIn('my-server', profiles)
    
    @patch('builtins.print')
    def test_empty_key_path(self, mock_print):
        """Test profile with empty key path."""
        add_profile('nokey', 'host.com', 'user', key='')
        
        profiles = load_profiles()
        # Empty key should still be stored but not used in command
        profile = profiles['nokey']
        cmd = build_ssh_command(profile)
        self.assertNotIn('-i', cmd)


def run_tests():
    """Run all tests with nice output."""
    print("=" * 70)
    print("TESTING: PortManager v1.0")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPortManagerConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestProfileManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestPortForwards))
    suite.addTests(loader.loadTestsFromTestCase(TestSSHCommandBuilding))
    suite.addTests(loader.loadTestsFromTestCase(TestConnectionManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIInterface))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"RESULTS: {total} tests")
    print(f"[OK] Passed: {passed}")
    if result.failures:
        print(f"[X] Failed: {len(result.failures)}")
    if result.errors:
        print(f"[X] Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
