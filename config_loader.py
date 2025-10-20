#!/usr/bin/env python3
"""
Configuration loader for the Rightmove scraper.

This module provides utilities to load and access configuration from
YAML files.
"""

import os
import yaml
from typing import Dict, Any, Optional


class ScraperConfig:
    """Configuration manager for the Rightmove scraper."""
    
    def __init__(self, config_path: str = "scraper_config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str): Path to the YAML configuration file
        """
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key_path (str): Dot-separated path to the configuration value
                           (e.g., 'selectors.property_cards.container')
            default (Any): Default value if key is not found
            
        Returns:
            Any: The configuration value
            
        Example:
            config = ScraperConfig()
            container_class = config.get('selectors.property_cards.container')
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_selectors(self) -> Dict[str, Any]:
        """Get all CSS selectors."""
        return self.get('selectors', {})
    
    def get_regex_patterns(self) -> Dict[str, Any]:
        """Get all regex patterns."""
        return self.get('regex_patterns', {})
    
    def get_url_patterns(self) -> Dict[str, Any]:
        """Get all URL patterns."""
        return self.get('url_patterns', {})
    
    def get_request_settings(self) -> Dict[str, Any]:
        """Get request settings."""
        return self.get('request_settings', {})
    
    def get_proxy_settings(self) -> Dict[str, Any]:
        """Get proxy settings."""
        return self.get('proxy_settings', {})
    
    def get_http_headers(self) -> Dict[str, str]:
        """Get HTTP headers as a dictionary suitable for requests."""
        headers_config = self.get('http_headers', {})
        
        # Convert YAML keys to proper HTTP header format
        headers = {}
        header_mapping = {
            'accept_language': 'Accept-Language',
            'accept': 'Accept',
            'connection': 'Connection',
            'dnt': 'DNT',
            'upgrade_insecure_requests': 'Upgrade-Insecure-Requests',
            'referer': 'Referer'
        }
        
        for yaml_key, value in headers_config.items():
            header_key = header_mapping.get(yaml_key, yaml_key)
            headers[header_key] = str(value)
        
        return headers
    
    def get_tor_proxies(self) -> Dict[str, str]:
        """Get Tor proxy configuration for requests."""
        tor_config = self.get('proxy_settings.tor', {})
        return {
            'http': tor_config.get('http', ''),
            'https': tor_config.get('https', '')
        }
    
    def get_data_processing_config(self) -> Dict[str, Any]:
        """Get data processing configuration."""
        return self.get('data_processing', {})
    
    def get_feature_extraction_config(self) -> Dict[str, Any]:
        """Get feature extraction configuration."""
        return self.get('feature_extraction', {})
    
    def get_file_patterns(self) -> Dict[str, Any]:
        """Get file naming patterns."""
        return self.get('file_patterns', {})
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config.copy() if self._config else {}


# Global configuration instance
_config_instance: Optional[ScraperConfig] = None


def get_config(config_path: str = "scraper_config.yaml") -> ScraperConfig:
    """
    Get the global configuration instance.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        ScraperConfig: The configuration instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ScraperConfig(config_path)
    
    return _config_instance


def reload_config() -> None:
    """Reload the global configuration."""
    global _config_instance
    
    if _config_instance is not None:
        _config_instance.reload()


if __name__ == "__main__":
    # Test the configuration loader
    config = get_config()
    
    print("=== Configuration Test ===")
    print(f"Website name: {config.get('website.name')}")
    print(f"Property cards selector: {config.get('selectors.property_cards.container')}")
    print(f"Page model regex: {config.get('regex_patterns.page_model.pattern')}")
    print(f"Tor HTTP proxy: {config.get('proxy_settings.tor.http')}")
    print(f"Request timeout: {config.get('request_settings.timeouts.page_request')}")
    print()
    print("HTTP Headers:")
    for key, value in config.get_http_headers().items():
        print(f"  {key}: {value}")
    print()
    print("Excluded fields:", config.get('data_processing.excluded_fields'))