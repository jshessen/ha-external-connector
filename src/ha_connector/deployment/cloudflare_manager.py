"""
CloudFlare Manager Module

Automates CloudFlare Access application creation and configuration for Home Assistant.
Replaces the bash cloudflare_manager.sh with a modern Python implementation.
"""

from __future__ import annotations

import os
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field

from ..utils import HAConnectorLogger, ValidationError, HAEnvironmentError


class CloudFlareConfig(BaseModel):
    """CloudFlare API configuration"""
    api_token: Optional[str] = Field(None, description="CloudFlare API token (recommended)")
    api_key: Optional[str] = Field(None, description="CloudFlare global API key")
    email: Optional[str] = Field(None, description="CloudFlare account email (required with API key)")
    zone_id: Optional[str] = Field(None, description="CloudFlare zone ID (optional)")
    debug: bool = Field(default=False, description="Enable debug logging")


class AccessApplicationConfig(BaseModel):
    """Configuration for CloudFlare Access application"""
    name: str = Field(..., description="Application name")
    domain: str = Field(..., description="Domain for the application")
    subdomain: Optional[str] = Field(None, description="Subdomain (if different from domain)")
    session_duration: str = Field(default="24h", description="Session duration")
    auto_redirect_to_identity: bool = Field(default=True, description="Auto redirect to identity provider")
    allowed_identity_providers: List[str] = Field(default_factory=list, description="Allowed identity providers")
    cors_headers: Optional[Dict[str, Any]] = Field(None, description="CORS headers configuration")
    service_auth_401_redirect: bool = Field(default=False, description="Service auth 401 redirect")
    tags: Optional[List[str]] = Field(None, description="Application tags")


class CloudFlareManager:
    """Manager for CloudFlare Access applications and configuration"""

    def __init__(self, config: Optional[CloudFlareConfig] = None):
        self.config = config or self._load_config_from_env()
        self.logger = HAConnectorLogger("cloudflare_manager", verbose=self.config.debug)
        self._validate_credentials()
        self._client = self._create_http_client()

    def _load_config_from_env(self) -> CloudFlareConfig:
        """Load CloudFlare configuration from environment variables"""
        return CloudFlareConfig(
            api_token=os.getenv('CF_API_TOKEN'),
            api_key=os.getenv('CF_API_KEY'),
            email=os.getenv('CF_EMAIL'),
            zone_id=os.getenv('CF_ZONE_ID'),
            debug=os.getenv('CF_DEBUG', 'false').lower() == 'true'
        )

    def _validate_credentials(self) -> None:
        """Validate CloudFlare credentials"""
        if not self.config.api_token:
            if not self.config.api_key or not self.config.email:
                raise HAEnvironmentError(
                    "CloudFlare credentials not found. Set either:\n"
                    "  CF_API_TOKEN=your_api_token (recommended)\n"
                    "Or:\n"
                    "  CF_API_KEY=your_global_api_key\n"
                    "  CF_EMAIL=your_email"
                )

    def _create_http_client(self) -> httpx.Client:
        """Create HTTP client with CloudFlare authentication"""
        headers = {
            'Content-Type': 'application/json',
        }

        if self.config.api_token:
            headers['Authorization'] = f'Bearer {self.config.api_token}'
        else:
            headers['X-Auth-Key'] = self.config.api_key
            headers['X-Auth-Email'] = self.config.email

        return httpx.Client(
            base_url='https://api.cloudflare.com/v4',
            headers=headers,
            timeout=30.0
        )

    def _debug(self, message: str) -> None:
        """Debug logging helper"""
        if self.config.debug:
            self.logger.debug(message)

    def get_zone_id(self, domain: str) -> str:
        """Get zone ID for a domain"""
        if self.config.zone_id:
            return self.config.zone_id

        self._debug(f"Getting zone ID for domain: {domain}")

        # Extract root domain (e.g., example.com from ha.example.com)
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            root_domain = '.'.join(domain_parts[-2:])
        else:
            root_domain = domain

        self._debug(f"Looking up zone for root domain: {root_domain}")

        response = self._client.get('/zones', params={'name': root_domain})
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            raise ValidationError(f"CloudFlare API error: {data.get('errors', [])}")

        zones = data.get('result', [])
        if not zones:
            raise ValidationError(f"No zone found for domain: {root_domain}")

        zone_id = zones[0]['id']
        self._debug(f"Found zone ID: {zone_id}")
        return zone_id

    def verify_domain_in_zone(self, domain: str, zone_id: str) -> bool:
        """Verify that a domain belongs to the specified zone"""
        self._debug(f"Verifying domain {domain} in zone {zone_id}")

        # Get zone details
        response = self._client.get(f'/zones/{zone_id}')
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            return False

        zone_name = data['result']['name']
        return domain.endswith(zone_name)

    def get_account_id(self) -> str:
        """Get CloudFlare account ID"""
        self._debug("Getting account ID")

        response = self._client.get('/accounts')
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            raise ValidationError(f"Failed to get account ID: {data.get('errors', [])}")

        accounts = data.get('result', [])
        if not accounts:
            raise ValidationError("No CloudFlare accounts found")

        account_id = accounts[0]['id']
        self._debug(f"Found account ID: {account_id}")
        return account_id

    def create_access_application(self, config: AccessApplicationConfig) -> Dict[str, Any]:
        """Create CloudFlare Access application"""
        self.logger.info(f"Creating Access application: {config.name}")

        # Get account ID
        account_id = self.get_account_id()

        # Prepare application data
        app_data = {
            'name': config.name,
            'domain': config.domain,
            'session_duration': config.session_duration,
            'auto_redirect_to_identity': config.auto_redirect_to_identity,
            'service_auth_401_redirect': config.service_auth_401_redirect,
        }

        if config.subdomain:
            app_data['domain'] = f"{config.subdomain}.{config.domain}"

        if config.allowed_identity_providers:
            app_data['allowed_identity_providers'] = config.allowed_identity_providers

        if config.cors_headers:
            app_data['cors_headers'] = config.cors_headers

        if config.tags:
            app_data['tags'] = config.tags

        self._debug(f"Creating application with data: {json.dumps(app_data, indent=2)}")

        # Create the application
        response = self._client.post(
            f'/accounts/{account_id}/access/apps',
            json=app_data
        )
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            errors = data.get('errors', [])
            raise ValidationError(f"Failed to create Access application: {errors}")

        application = data['result']
        self.logger.success(f"Created Access application: {config.name} (ID: {application['id']})")

        return application

    def get_access_application(self, app_id: str) -> Dict[str, Any]:
        """Get CloudFlare Access application by ID"""
        account_id = self.get_account_id()

        response = self._client.get(f'/accounts/{account_id}/access/apps/{app_id}')
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            raise ValidationError(f"Failed to get Access application: {data.get('errors', [])}")

        return data['result']

    def list_access_applications(self) -> List[Dict[str, Any]]:
        """List all CloudFlare Access applications"""
        account_id = self.get_account_id()

        response = self._client.get(f'/accounts/{account_id}/access/apps')
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            raise ValidationError(f"Failed to list Access applications: {data.get('errors', [])}")

        return data['result']

    def update_access_application(self, app_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update CloudFlare Access application"""
        account_id = self.get_account_id()

        self.logger.info(f"Updating Access application: {app_id}")

        response = self._client.put(
            f'/accounts/{account_id}/access/apps/{app_id}',
            json=updates
        )
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            raise ValidationError(f"Failed to update Access application: {data.get('errors', [])}")

        self.logger.success(f"Updated Access application: {app_id}")
        return data['result']

    def delete_access_application(self, app_id: str) -> bool:
        """Delete CloudFlare Access application"""
        account_id = self.get_account_id()

        self.logger.info(f"Deleting Access application: {app_id}")

        response = self._client.delete(f'/accounts/{account_id}/access/apps/{app_id}')
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            raise ValidationError(f"Failed to delete Access application: {data.get('errors', [])}")

        self.logger.success(f"Deleted Access application: {app_id}")
        return True

    def create_dns_record(self, zone_id: str, record_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create DNS record in CloudFlare"""
        self.logger.info(f"Creating DNS record: {record_config.get('name')}")

        response = self._client.post(
            f'/zones/{zone_id}/dns_records',
            json=record_config
        )
        response.raise_for_status()

        data = response.json()
        if not data.get('success', False):
            raise ValidationError(f"Failed to create DNS record: {data.get('errors', [])}")

        record = data['result']
        self.logger.success(f"Created DNS record: {record['name']} -> {record['content']}")

        return record

    def setup_ha_proxy(self,
                      ha_domain: str,
                      lambda_url: str,
                      application_name: str = "Home Assistant") -> Dict[str, Any]:
        """Set up complete CloudFlare Access proxy for Home Assistant"""
        self.logger.info(f"Setting up CloudFlare Access proxy for: {ha_domain}")

        # Create Access application
        app_config = AccessApplicationConfig(
            name=application_name,
            domain=ha_domain,
            session_duration="24h",
            auto_redirect_to_identity=True
        )

        application = self.create_access_application(app_config)

        # Get zone ID and create DNS record pointing to Lambda
        zone_id = self.get_zone_id(ha_domain)

        # Extract hostname from Lambda URL
        lambda_hostname = lambda_url.replace('https://', '').replace('http://', '').split('/')[0]

        dns_config = {
            'type': 'CNAME',
            'name': ha_domain,
            'content': lambda_hostname,
            'ttl': 1,  # Auto TTL
            'proxied': True  # Enable CloudFlare proxy
        }

        try:
            dns_record = self.create_dns_record(zone_id, dns_config)

            self.logger.success(f"Successfully set up CloudFlare Access proxy")
            self.logger.info(f"Application ID: {application['id']}")
            self.logger.info(f"DNS Record ID: {dns_record['id']}")
            self.logger.info(f"Access URL: https://{ha_domain}")

            return {
                'application': application,
                'dns_record': dns_record,
                'access_url': f"https://{ha_domain}"
            }

        except Exception as e:
            # Clean up application if DNS setup failed
            try:
                self.delete_access_application(application['id'])
            except Exception:
                pass
            raise e

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, '_client'):
            self._client.close()


def create_access_application(domain: str,
                            application_name: str = "Home Assistant",
                            lambda_url: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to create CloudFlare Access application"""
    with CloudFlareManager() as cf_manager:
        if lambda_url:
            return cf_manager.setup_ha_proxy(domain, lambda_url, application_name)
        else:
            app_config = AccessApplicationConfig(
                name=application_name,
                domain=domain
            )
            return cf_manager.create_access_application(app_config)
