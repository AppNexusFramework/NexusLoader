#!/usr/bin/env python3
"""
Nexus Enterprise License System
================================
Advanced licensing system for binary protection with:
- Hardware fingerprinting
- Online license validation
- Time-based licenses
- Feature-based licensing
- Anti-tampering protection
- Offline grace period

Author: Mauro Tommasi
Version: 1.0.0
License: Proprietary
"""

import os
import sys
import json
import time
import hashlib
import uuid
import platform
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import base64
from pathlib import Path
import hmac
import secrets

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import requests
except ImportError:
    print("Error: Required dependencies not installed")
    print("Run: pip install cryptography requests")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

class LicenseConfig:
    """License system configuration"""
    
    # License server URL (change to your server)
    LICENSE_SERVER_URL = "https://license.yourcompany.com/api/v1"
    
    # License file location
    LICENSE_FILE = ".nexus_license"
    LICENSE_DIR = os.path.expanduser("~/.nexus")
    
    # Grace period for offline validation (days)
    OFFLINE_GRACE_PERIOD = 7
    
    # Online validation interval (hours)
    ONLINE_CHECK_INTERVAL = 24
    
    # Encryption key (CHANGE THIS IN PRODUCTION!)
    # Generate with: Fernet.generate_key()
    ENCRYPTION_KEY = b'YOUR_ENCRYPTION_KEY_HERE_CHANGE_THIS_IN_PRODUCTION'
    
    # Product information
    PRODUCT_NAME = "NexusSkyTransform"
    PRODUCT_VERSION = "1.0.0"
    
    # Feature flags
    FEATURES = {
        "basic": ["transform", "import", "export"],
        "professional": ["transform", "import", "export", "api", "batch"],
        "enterprise": ["transform", "import", "export", "api", "batch", "cloud", "advanced"]
    }


# =============================================================================
# HARDWARE FINGERPRINTING
# =============================================================================

class HardwareFingerprint:
    """Generate unique hardware fingerprint"""
    
    @staticmethod
    def get_machine_id() -> str:
        """Get unique machine identifier"""
        try:
            # Try to get machine-id (Linux)
            if os.path.exists('/etc/machine-id'):
                with open('/etc/machine-id', 'r') as f:
                    return f.read().strip()
            
            # Try systemd machine-id
            if os.path.exists('/var/lib/dbus/machine-id'):
                with open('/var/lib/dbus/machine-id', 'r') as f:
                    return f.read().strip()
            
            # Windows - use wmic
            if platform.system() == 'Windows':
                output = subprocess.check_output(
                    'wmic csproduct get uuid',
                    shell=True
                ).decode().split('\n')[1].strip()
                return output
            
            # macOS - use IOPlatformUUID
            if platform.system() == 'Darwin':
                output = subprocess.check_output(
                    'ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID',
                    shell=True
                ).decode().split('"')[3]
                return output
            
        except:
            pass
        
        # Fallback to MAC address
        return str(uuid.getnode())
    
    @staticmethod
    def get_cpu_info() -> str:
        """Get CPU information"""
        try:
            if platform.system() == 'Windows':
                output = subprocess.check_output(
                    'wmic cpu get ProcessorId',
                    shell=True
                ).decode().split('\n')[1].strip()
                return output
            elif platform.system() == 'Linux':
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'Serial' in line:
                            return line.split(':')[1].strip()
            elif platform.system() == 'Darwin':
                output = subprocess.check_output(
                    'sysctl -n machdep.cpu.brand_string',
                    shell=True
                ).decode().strip()
                return output
        except:
            pass
        
        return platform.processor()
    
    @staticmethod
    def get_disk_serial() -> str:
        """Get disk serial number"""
        try:
            if platform.system() == 'Windows':
                output = subprocess.check_output(
                    'wmic diskdrive get serialnumber',
                    shell=True
                ).decode().split('\n')[1].strip()
                return output
            elif platform.system() == 'Linux':
                output = subprocess.check_output(
                    'lsblk -o SERIAL -n | head -n1',
                    shell=True
                ).decode().strip()
                return output
            elif platform.system() == 'Darwin':
                output = subprocess.check_output(
                    'system_profiler SPSerialATADataType | grep "Serial Number"',
                    shell=True
                ).decode().split(':')[1].strip()
                return output
        except:
            pass
        
        return "UNKNOWN"
    
    @classmethod
    def generate_fingerprint(cls) -> str:
        """Generate unique hardware fingerprint"""
        machine_id = cls.get_machine_id()
        cpu_info = cls.get_cpu_info()
        disk_serial = cls.get_disk_serial()
        hostname = platform.node()
        system = platform.system()
        
        # Combine all information
        combined = f"{machine_id}|{cpu_info}|{disk_serial}|{hostname}|{system}"
        
        # Generate hash
        fingerprint = hashlib.sha256(combined.encode()).hexdigest()
        
        return fingerprint


# =============================================================================
# LICENSE DATA STRUCTURE
# =============================================================================

class LicenseData:
    """License data structure"""
    
    def __init__(self, data: Dict[str, Any]):
        self.license_key = data.get('license_key')
        self.customer_name = data.get('customer_name')
        self.customer_email = data.get('customer_email')
        self.company = data.get('company')
        self.product = data.get('product')
        self.version = data.get('version')
        self.license_type = data.get('license_type')  # trial, standard, professional, enterprise
        self.features = data.get('features', [])
        self.max_users = data.get('max_users', 1)
        self.hardware_id = data.get('hardware_id')
        self.issued_date = data.get('issued_date')
        self.expiry_date = data.get('expiry_date')
        self.last_validated = data.get('last_validated')
        self.activation_count = data.get('activation_count', 0)
        self.max_activations = data.get('max_activations', 1)
        self.is_trial = data.get('is_trial', False)
        self.is_floating = data.get('is_floating', False)
        self.offline_mode = data.get('offline_mode', False)
        self.metadata = data.get('metadata', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'license_key': self.license_key,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'company': self.company,
            'product': self.product,
            'version': self.version,
            'license_type': self.license_type,
            'features': self.features,
            'max_users': self.max_users,
            'hardware_id': self.hardware_id,
            'issued_date': self.issued_date,
            'expiry_date': self.expiry_date,
            'last_validated': self.last_validated,
            'activation_count': self.activation_count,
            'max_activations': self.max_activations,
            'is_trial': self.is_trial,
            'is_floating': self.is_floating,
            'offline_mode': self.offline_mode,
            'metadata': self.metadata
        }


# =============================================================================
# LICENSE MANAGER
# =============================================================================

class LicenseManager:
    """Main license management system"""
    
    def __init__(self, config: LicenseConfig = None):
        self.config = config or LicenseConfig()
        self.fernet = Fernet(self.config.ENCRYPTION_KEY)
        self.hardware_fp = HardwareFingerprint.generate_fingerprint()
        self.license_file_path = os.path.join(
            self.config.LICENSE_DIR,
            self.config.LICENSE_FILE
        )
        
        # Create license directory if it doesn't exist
        os.makedirs(self.config.LICENSE_DIR, exist_ok=True)
    
    def generate_license_key(self, customer_email: str) -> str:
        """Generate a unique license key"""
        timestamp = str(int(time.time()))
        random_part = secrets.token_hex(8)
        
        combined = f"{customer_email}|{timestamp}|{random_part}"
        hash_part = hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
        
        # Format: XXXX-XXXX-XXXX-XXXX
        key = f"{hash_part[0:4]}-{hash_part[4:8]}-{hash_part[8:12]}-{hash_part[12:16]}"
        
        return key
    
    def encrypt_license(self, license_data: LicenseData) -> str:
        """Encrypt license data"""
        json_data = json.dumps(license_data.to_dict())
        encrypted = self.fernet.encrypt(json_data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_license(self, encrypted_data: str) -> LicenseData:
        """Decrypt license data"""
        try:
            encrypted = base64.b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted)
            data = json.loads(decrypted.decode())
            return LicenseData(data)
        except Exception as e:
            raise ValueError(f"Invalid license data: {e}")
    
    def save_license(self, license_data: LicenseData):
        """Save license to file"""
        encrypted = self.encrypt_license(license_data)
        
        with open(self.license_file_path, 'w') as f:
            f.write(encrypted)
        
        # Make file read-only
        os.chmod(self.license_file_path, 0o400)
    
    def load_license(self) -> Optional[LicenseData]:
        """Load license from file"""
        if not os.path.exists(self.license_file_path):
            return None
        
        try:
            with open(self.license_file_path, 'r') as f:
                encrypted = f.read()
            
            return self.decrypt_license(encrypted)
        except Exception as e:
            print(f"Error loading license: {e}")
            return None
    
    def activate_license(
        self,
        license_key: str,
        customer_email: str,
        online: bool = True
    ) -> bool:
        """Activate a license"""
        try:
            if online:
                # Online activation
                response = requests.post(
                    f"{self.config.LICENSE_SERVER_URL}/activate",
                    json={
                        'license_key': license_key,
                        'customer_email': customer_email,
                        'hardware_id': self.hardware_fp,
                        'product': self.config.PRODUCT_NAME,
                        'version': self.config.PRODUCT_VERSION,
                        'platform': platform.system(),
                        'hostname': platform.node()
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    license_data = LicenseData(data['license'])
                    license_data.last_validated = datetime.now().isoformat()
                    self.save_license(license_data)
                    return True
                else:
                    print(f"Activation failed: {response.json().get('error', 'Unknown error')}")
                    return False
            else:
                # Offline activation (requires pre-generated license file)
                print("Offline activation not implemented yet")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Network error during activation: {e}")
            print("Please check your internet connection or contact support")
            return False
        except Exception as e:
            print(f"Activation error: {e}")
            return False
    
    def validate_license(self, online_check: bool = True) -> tuple[bool, str]:
        """
        Validate license
        Returns: (is_valid, message)
        """
        # Load license
        license_data = self.load_license()
        
        if not license_data:
            return False, "No license found. Please activate your license."
        
        # Check hardware fingerprint
        if license_data.hardware_id != self.hardware_fp:
            return False, "License is not valid for this machine."
        
        # Check product
        if license_data.product != self.config.PRODUCT_NAME:
            return False, "License is for a different product."
        
        # Check expiry date
        if license_data.expiry_date:
            expiry = datetime.fromisoformat(license_data.expiry_date)
            if datetime.now() > expiry:
                return False, f"License expired on {expiry.strftime('%Y-%m-%d')}."
        
        # Check if online validation is needed
        if online_check and not license_data.offline_mode:
            last_validated = datetime.fromisoformat(license_data.last_validated)
            hours_since_validation = (datetime.now() - last_validated).total_seconds() / 3600
            
            if hours_since_validation > self.config.ONLINE_CHECK_INTERVAL:
                # Perform online validation
                valid, message = self._validate_online(license_data)
                if not valid:
                    # Check grace period
                    days_offline = hours_since_validation / 24
                    if days_offline > self.config.OFFLINE_GRACE_PERIOD:
                        return False, f"License validation failed. {message}"
                    else:
                        print(f"Warning: Could not validate license online. Grace period: {self.config.OFFLINE_GRACE_PERIOD - int(days_offline)} days remaining.")
                else:
                    # Update last validated
                    license_data.last_validated = datetime.now().isoformat()
                    self.save_license(license_data)
        
        return True, "License is valid."
    
    def _validate_online(self, license_data: LicenseData) -> tuple[bool, str]:
        """Perform online license validation"""
        try:
            response = requests.post(
                f"{self.config.LICENSE_SERVER_URL}/validate",
                json={
                    'license_key': license_data.license_key,
                    'hardware_id': self.hardware_fp,
                    'product': self.config.PRODUCT_NAME
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    return True, "License validated successfully."
                else:
                    return False, data.get('message', 'License is not valid.')
            else:
                return False, "Validation server error."
                
        except requests.exceptions.RequestException:
            return False, "Could not connect to validation server."
    
    def check_feature(self, feature: str) -> bool:
        """Check if a feature is enabled in the license"""
        license_data = self.load_license()
        
        if not license_data:
            return False
        
        return feature in license_data.features
    
    def get_license_info(self) -> Dict[str, Any]:
        """Get license information"""
        license_data = self.load_license()
        
        if not license_data:
            return {
                'licensed': False,
                'message': 'No license found'
            }
        
        expiry_date = None
        days_remaining = None
        
        if license_data.expiry_date:
            expiry = datetime.fromisoformat(license_data.expiry_date)
            expiry_date = expiry.strftime('%Y-%m-%d')
            days_remaining = (expiry - datetime.now()).days
        
        return {
            'licensed': True,
            'customer_name': license_data.customer_name,
            'company': license_data.company,
            'license_type': license_data.license_type,
            'features': license_data.features,
            'expiry_date': expiry_date,
            'days_remaining': days_remaining,
            'is_trial': license_data.is_trial,
            'product': license_data.product,
            'version': license_data.version
        }
    
    def deactivate_license(self) -> bool:
        """Deactivate and remove license"""
        try:
            license_data = self.load_license()
            
            if license_data:
                # Notify server
                try:
                    requests.post(
                        f"{self.config.LICENSE_SERVER_URL}/deactivate",
                        json={
                            'license_key': license_data.license_key,
                            'hardware_id': self.hardware_fp
                        },
                        timeout=5
                    )
                except:
                    pass  # Continue even if server notification fails
            
            # Remove license file
            if os.path.exists(self.license_file_path):
                os.remove(self.license_file_path)
            
            return True
        except Exception as e:
            print(f"Error deactivating license: {e}")
            return False


# =============================================================================
# LICENSE DECORATOR FOR FUNCTIONS
# =============================================================================

def require_license(feature: str = None):
    """
    Decorator to protect functions with license check
    
    Usage:
        @require_license()
        def my_function():
            pass
        
        @require_license(feature='api')
        def api_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            license_manager = LicenseManager()
            
            # Validate license
            valid, message = license_manager.validate_license()
            
            if not valid:
                print(f"License Error: {message}")
                print("Please contact sales@yourcompany.com to purchase a license.")
                sys.exit(1)
            
            # Check feature if specified
            if feature and not license_manager.check_feature(feature):
                print(f"Feature '{feature}' is not available in your license.")
                print("Please upgrade your license to access this feature.")
                sys.exit(1)
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def cli_activate():
    """CLI command to activate license"""
    print("=== Nexus License Activation ===\n")
    
    license_key = input("Enter your license key: ").strip()
    customer_email = input("Enter your email: ").strip()
    
    print("\nActivating license...")
    
    manager = LicenseManager()
    success = manager.activate_license(license_key, customer_email)
    
    if success:
        print("\n✓ License activated successfully!")
        print("\nLicense Information:")
        info = manager.get_license_info()
        for key, value in info.items():
            if value:
                print(f"  {key}: {value}")
    else:
        print("\n✗ License activation failed.")
        print("Please check your license key and try again.")
        print("If the problem persists, contact support@yourcompany.com")


def cli_status():
    """CLI command to check license status"""
    manager = LicenseManager()
    
    print("=== Nexus License Status ===\n")
    
    valid, message = manager.validate_license(online_check=False)
    
    if valid:
        print("✓ License Status: VALID\n")
        info = manager.get_license_info()
        
        print(f"Customer: {info.get('customer_name')}")
        if info.get('company'):
            print(f"Company: {info.get('company')}")
        print(f"License Type: {info.get('license_type', 'Unknown').upper()}")
        print(f"Product: {info.get('product')}")
        
        if info.get('is_trial'):
            print("\n⚠ This is a TRIAL license")
        
        if info.get('expiry_date'):
            print(f"\nExpiry Date: {info.get('expiry_date')}")
            days = info.get('days_remaining')
            if days is not None:
                if days > 0:
                    print(f"Days Remaining: {days}")
                else:
                    print("Status: EXPIRED")
        else:
            print("\nLicense Type: Perpetual")
        
        print(f"\nEnabled Features:")
        for feature in info.get('features', []):
            print(f"  • {feature}")
    else:
        print(f"✗ License Status: INVALID\n")
        print(f"Reason: {message}")
        print("\nTo activate a license, run:")
        print("  python app/NexusSkyTransform.py --activate-license")


def cli_deactivate():
    """CLI command to deactivate license"""
    print("=== Nexus License Deactivation ===\n")
    
    confirm = input("Are you sure you want to deactivate this license? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        manager = LicenseManager()
        if manager.deactivate_license():
            print("\n✓ License deactivated successfully.")
        else:
            print("\n✗ Failed to deactivate license.")
    else:
        print("\nDeactivation cancelled.")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Nexus License Manager")
    parser.add_argument('--activate', action='store_true', help='Activate license')
    parser.add_argument('--status', action='store_true', help='Check license status')
    parser.add_argument('--deactivate', action='store_true', help='Deactivate license')
    parser.add_argument('--hardware-id', action='store_true', help='Show hardware ID')
    
    args = parser.parse_args()
    
    if args.activate:
        cli_activate()
    elif args.status:
        cli_status()
    elif args.deactivate:
        cli_deactivate()
    elif args.hardware_id:
        print(f"Hardware ID: {HardwareFingerprint.generate_fingerprint()}")
    else:
        parser.print_help()