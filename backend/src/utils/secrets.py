"""
Secrets rotation mechanism for secure credential management.

Per Constitution Security requirements:
- Secure storage of sensitive data
- Periodic rotation of secrets
- Version tracking for rollback capability
- Audit logging of secret access
- Secure secret distribution
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import base64
import hashlib
from dataclasses import dataclass, field
from enum import Enum

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os


logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    """Enumeration of secret types."""
    DATABASE_URL = "database_url"
    OPENAI_API_KEY = "openai_api_key"
    GMAIL_CREDENTIALS = "gmail_credentials"
    TWILIO_ACCOUNT_SID = "twilio_account_sid"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"
    EMAIL_SMTP_URL = "email_smtp_url"
    API_SECRET_KEY = "api_secret_key"


@dataclass
class SecretVersion:
    """Represents a version of a secret."""

    version_id: str
    secret_value: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    rotation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'version_id': self.version_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'rotation_reason': self.rotation_reason
        }


@dataclass
class SecretRecord:
    """Represents a secret with all its versions."""

    secret_type: SecretType
    versions: List[SecretVersion] = field(default_factory=list)
    rotation_period_days: int = 90  # Default 90 days

    def get_active_version(self) -> Optional[SecretVersion]:
        """Get the currently active version."""
        for version in self.versions:
            if version.is_active:
                return version
        return None

    def get_latest_version(self) -> Optional[SecretVersion]:
        """Get the most recent version."""
        if not self.versions:
            return None
        return self.versions[-1]

    def should_rotate(self) -> bool:
        """Check if secret should be rotated."""
        active_version = self.get_active_version()
        if not active_version:
            return True

        # Check if expired
        if active_version.expires_at and datetime.now() >= active_version.expires_at:
            return True

        # Check rotation period
        days_since_creation = (datetime.now() - active_version.created_at).days
        return days_since_creation >= self.rotation_period_days


class SecretsManager:
    """
    Secrets manager with rotation support.

    Features:
    - Encrypted secret storage
    - Automatic rotation scheduling
    - Version tracking
    - Audit logging
    - Rollback capability
    """

    def __init__(
        self,
        secrets_file: str = "secrets.enc",
        master_key_env_var: str = "SECRETS_MASTER_KEY",
        default_rotation_days: int = 90
    ):
        """
        Initialize secrets manager.

        Args:
            secrets_file: Path to encrypted secrets file
            master_key_env_var: Environment variable containing master key
            default_rotation_days: Default rotation period in days
        """
        self.secrets_file = Path(secrets_file)
        self.master_key_env_var = master_key_env_var
        self.default_rotation_days = default_rotation_days

        # Load master key
        self.master_key = self._load_master_key()
        if not self.master_key:
            raise ValueError("Master key not found in environment variables")

        # Create cipher
        self.cipher = Fernet(self.master_key)

        # Load secrets
        self.secrets: Dict[SecretType, SecretRecord] = {}
        self._load_secrets()

        # Audit log
        self.audit_log: List[Dict[str, Any]] = []

        logger.info("Secrets manager initialized")

    def _load_master_key(self) -> Optional[str]:
        """
        Load master key from environment.

        Returns:
            Master key or None
        """
        import os
        return os.environ.get(self.master_key_env_var)

    def _encrypt_secret(self, secret: str) -> str:
        """
        Encrypt a secret.

        Args:
            secret: Secret value to encrypt

        Returns:
            Encrypted secret
        """
        return self.cipher.encrypt(secret.encode()).decode()

    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt a secret.

        Args:
            encrypted_secret: Encrypted secret

        Returns:
            Decrypted secret
        """
        return self.cipher.decrypt(encrypted_secret.encode()).decode()

    def _generate_version_id(self, secret_type: SecretType) -> str:
        """
        Generate unique version ID.

        Args:
            secret_type: Secret type

        Returns:
            Version ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_bytes = os.urandom(4)
        hash_obj = hashlib.sha256(random_bytes)
        return f"{secret_type.value}_{timestamp}_{hash_obj.hexdigest()[:8]}"

    def _load_secrets(self):
        """Load secrets from encrypted file."""
        if not self.secrets_file.exists():
            logger.warning("Secrets file not found, creating new")
            return

        try:
            with open(self.secrets_file, 'r') as f:
                encrypted_data = f.read()

            # Decrypt
            decrypted_data = self._decrypt_secret(encrypted_data)
            secrets_dict = json.loads(decrypted_data)

            # Reconstruct secret records
            for secret_type_str, secret_data in secrets_dict.items():
                secret_type = SecretType(secret_type_str)

                versions = []
                for version_data in secret_data.get('versions', []):
                    version = SecretVersion(
                        version_id=version_data['version_id'],
                        secret_value=self._encrypt_secret(version_data['secret_value']),
                        created_at=datetime.fromisoformat(version_data['created_at']),
                        expires_at=datetime.fromisoformat(version_data['expires_at']) if version_data.get('expires_at') else None,
                        is_active=version_data.get('is_active', True),
                        rotation_reason=version_data.get('rotation_reason')
                    )
                    versions.append(version)

                secret_record = SecretRecord(
                    secret_type=secret_type,
                    versions=versions,
                    rotation_period_days=secret_data.get('rotation_period_days', self.default_rotation_days)
                )

                self.secrets[secret_type] = secret_record

            logger.info(f"Loaded {len(self.secrets)} secrets from file")

        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            self.secrets = {}

    def _save_secrets(self):
        """Save secrets to encrypted file."""
        secrets_dict = {}

        for secret_type, secret_record in self.secrets.items():
            versions_data = []

            for version in secret_record.versions:
                versions_data.append({
                    'version_id': version.version_id,
                    'secret_value': self._decrypt_secret(version.secret_value),
                    'created_at': version.created_at.isoformat(),
                    'expires_at': version.expires_at.isoformat() if version.expires_at else None,
                    'is_active': version.is_active,
                    'rotation_reason': version.rotation_reason
                })

            secrets_dict[secret_type.value] = {
                'versions': versions_data,
                'rotation_period_days': secret_record.rotation_period_days
            }

        try:
            # Serialize
            secrets_json = json.dumps(secrets_dict, indent=2)

            # Encrypt
            encrypted_data = self._encrypt_secret(secrets_json)

            # Save
            self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.secrets_file, 'w') as f:
                f.write(encrypted_data)

            logger.info("Secrets saved to file")

        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")
            raise

    def set_secret(
        self,
        secret_type: SecretType,
        secret_value: str,
        rotation_period_days: Optional[int] = None
    ):
        """
        Set or update a secret.

        Args:
            secret_type: Type of secret
            secret_value: Secret value
            rotation_period_days: Rotation period in days
        """
        # Get or create secret record
        if secret_type in self.secrets:
            secret_record = self.secrets[secret_type]
        else:
            secret_record = SecretRecord(
                secret_type=secret_type,
                rotation_period_days=rotation_period_days or self.default_rotation_days
            )
            self.secrets[secret_type] = secret_record

        # Deactivate previous versions
        for version in secret_record.versions:
            version.is_active = False

        # Create new version
        version_id = self._generate_version_id(secret_type)
        new_version = SecretVersion(
            version_id=version_id,
            secret_value=self._encrypt_secret(secret_value),
            created_at=datetime.now(),
            is_active=True
        )

        secret_record.versions.append(new_version)

        # Save
        self._save_secrets()

        # Log
        self.audit_log.append({
            'action': 'set_secret',
            'secret_type': secret_type.value,
            'version_id': version_id,
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"Secret set: {secret_type.value}, version: {version_id}")

    def get_secret(self, secret_type: SecretType) -> Optional[str]:
        """
        Get active secret value.

        Args:
            secret_type: Type of secret

        Returns:
            Secret value or None if not found
        """
        secret_record = self.secrets.get(secret_type)
        if not secret_record:
            logger.warning(f"Secret not found: {secret_type.value}")
            return None

        active_version = secret_record.get_active_version()
        if not active_version:
            logger.warning(f"No active version for secret: {secret_type.value}")
            return None

        # Log access
        self.audit_log.append({
            'action': 'get_secret',
            'secret_type': secret_type.value,
            'version_id': active_version.version_id,
            'timestamp': datetime.now().isoformat()
        })

        return self._decrypt_secret(active_version.secret_value)

    def rotate_secret(
        self,
        secret_type: SecretType,
        new_value: str,
        reason: Optional[str] = None
    ):
        """
        Rotate a secret to a new value.

        Args:
            secret_type: Type of secret to rotate
            new_value: New secret value
            reason: Reason for rotation
        """
        if secret_type not in self.secrets:
            raise ValueError(f"Secret not found: {secret_type.value}")

        secret_record = self.secrets[secret_type]

        # Deactivate previous versions
        for version in secret_record.versions:
            version.is_active = False

        # Create new version
        version_id = self._generate_version_id(secret_type)
        new_version = SecretVersion(
            version_id=version_id,
            secret_value=self._encrypt_secret(new_value),
            created_at=datetime.now(),
            is_active=True,
            rotation_reason=reason
        )

        secret_record.versions.append(new_version)

        # Save
        self._save_secrets()

        # Log
        self.audit_log.append({
            'action': 'rotate_secret',
            'secret_type': secret_type.value,
            'old_version_id': secret_record.versions[-2].version_id if len(secret_record.versions) > 1 else None,
            'new_version_id': version_id,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"Secret rotated: {secret_type.value}, version: {version_id}")

    def rollback_secret(
        self,
        secret_type: SecretType,
        version_id: str
    ):
        """
        Rollback secret to a previous version.

        Args:
            secret_type: Type of secret
            version_id: Version ID to rollback to
        """
        if secret_type not in self.secrets:
            raise ValueError(f"Secret not found: {secret_type.value}")

        secret_record = self.secrets[secret_type]

        # Find target version
        target_version = None
        for version in secret_record.versions:
            if version.version_id == version_id:
                target_version = version
                break

        if not target_version:
            raise ValueError(f"Version not found: {version_id}")

        # Deactivate all versions
        for version in secret_record.versions:
            version.is_active = False

        # Activate target version
        target_version.is_active = True

        # Save
        self._save_secrets()

        # Log
        self.audit_log.append({
            'action': 'rollback_secret',
            'secret_type': secret_type.value,
            'version_id': version_id,
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"Secret rolled back: {secret_type.value}, version: {version_id}")

    def check_rotations(self) -> List[SecretType]:
        """
        Check which secrets need rotation.

        Returns:
            List of secret types that need rotation
        """
        secrets_to_rotate = []

        for secret_type, secret_record in self.secrets.items():
            if secret_record.should_rotate():
                secrets_to_rotate.append(secret_type)

        return secrets_to_rotate

    def get_secret_versions(self, secret_type: SecretType) -> List[Dict[str, Any]]:
        """
        Get all versions of a secret.

        Args:
            secret_type: Type of secret

        Returns:
            List of version information
        """
        if secret_type not in self.secrets:
            return []

        secret_record = self.secrets[secret_type]
        return [version.to_dict() for version in secret_record.versions]

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit log entries.

        Args:
            limit: Maximum number of entries

        Returns:
            List of audit log entries
        """
        return self.audit_log[-limit:]


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """
    Get global secrets manager instance.

    Returns:
        SecretsManager instance

    Raises:
        ValueError: If master key not found
    """
    global _secrets_manager

    if _secrets_manager is None:
        _secrets_manager = SecretsManager()

    return _secrets_manager
