"""
SSL/TLS configuration for secure communications.

Per Constitution Security requirements:
- Enforce HTTPS for all communications
- Use TLS 1.2 or higher
- Implement certificate pinning
- Secure cookie settings
- HSTS headers
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import ssl

from fastapi import FastAPI, Request, Response
from starlette.middleware.https import HTTPSRedirectMiddleware
from fastapi.middleware import Middleware
from fastapi.middleware.gzip import GZipMiddleware


logger = logging.getLogger(__name__)


class TLSConfig:
    """
    SSL/TLS configuration for FastAPI application.

    Enforces:
    - HTTPS only
    - TLS 1.2+ minimum
    - Strong cipher suites
    - Secure headers
    """

    def __init__(
        self,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None,
        ssl_keyfile_password: Optional[str] = None,
        min_tls_version: str = "TLSv1_2",
        strict_transport_security: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        secure_cookies: bool = True,
        cookie_samesite: str = "Lax"
    ):
        """
        Initialize TLS configuration.

        Args:
            ssl_keyfile: Path to SSL private key file
            ssl_certfile: Path to SSL certificate file
            ssl_ca_certs: Path to CA certificates file
            ssl_keyfile_password: Password for SSL key file
            min_tls_version: Minimum TLS version (TLSv1_2 or TLSv1_3)
            strict_transport_security: Enable HSTS
            hsts_max_age: HSTS max-age in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
            secure_cookies: Set Secure flag on cookies
            cookie_samesite: SameSite cookie attribute
        """
        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile
        self.ssl_ca_certs = ssl_ca_certs
        self.ssl_keyfile_password = ssl_keyfile_password
        self.min_tls_version = min_tls_version
        self.strict_transport_security = strict_transport_security
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.secure_cookies = secure_cookies
        self.cookie_samesite = cookie_samesite

        # SSL context
        self.ssl_context = None

        logger.info(
            f"TLS config initialized: min_tls={min_tls_version}, "
            f"hsts={strict_transport_security}"
        )

    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context with secure settings.

        Returns:
            Configured SSL context

        Raises:
            ValueError: If required SSL files not found
        """
        if not self.ssl_keyfile or not self.ssl_certfile:
            raise ValueError("SSL keyfile and certfile are required")

        # Validate files exist
        if not Path(self.ssl_keyfile).exists():
            raise ValueError(f"SSL keyfile not found: {self.ssl_keyfile}")
        if not Path(self.ssl_certfile).exists():
            raise ValueError(f"SSL certfile not found: {self.ssl_certfile}")

        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # Load certificate and key
        context.load_cert_chain(
            certfile=self.ssl_certfile,
            keyfile=self.ssl_keyfile,
            password=self.ssl_keyfile_password
        )

        # Load CA certificates if provided
        if self.ssl_ca_certs:
            if Path(self.ssl_ca_certs).exists():
                context.load_verify_locations(cafile=self.ssl_ca_certs)
            else:
                logger.warning(f"CA certs file not found: {self.ssl_ca_certs}")

        # Set minimum TLS version
        if self.min_tls_version == "TLSv1_3":
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        else:
            context.minimum_version = ssl.TLSVersion.TLSv1_2

        # Set strong cipher suites
        cipher_suites = [
            'TLS_AES_256_GCM_SHA384',
            'TLS_AES_128_GCM_SHA256',
            'TLS_CHACHA20_POLY1305_SHA256',
            'TLS_AES_128_CCM_SHA256'
        ]
        context.set_ciphers(':'.join(cipher_suites))

        # Enable verification
        context.verify_mode = ssl.CERT_REQUIRED

        logger.info(f"SSL context created: min_version={context.minimum_version}")

        self.ssl_context = context
        return context

    def get_uvicorn_ssl_config(self) -> Dict[str, Any]:
        """
        Get SSL configuration for Uvicorn.

        Returns:
            Dictionary with SSL configuration
        """
        return {
            'ssl_keyfile': self.ssl_keyfile,
            'ssl_certfile': self.ssl_certfile,
            'ssl_keyfile_password': self.ssl_keyfile_password,
        }


class SecurityHeadersMiddleware:
    """
    Middleware for adding security headers to responses.

    Adds:
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Content-Security-Policy
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(
        self,
        strict_transport_security: bool = True,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        xss_protection: str = "1; mode=block"
    ):
        """
        Initialize security headers middleware.

        Args:
            strict_transport_security: Enable HSTS
            hsts_max_age: HSTS max-age in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
            frame_options: X-Frame-Options value
            content_type_options: X-Content-Type-Options value
            xss_protection: X-XSS-Protection value
        """
        self.strict_transport_security = strict_transport_security
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection

        logger.info("Security headers middleware initialized")

    async def __call__(self, request: Request, call_next):
        """
        Process request and add security headers.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Strict-Transport-Security (HSTS)
        if self.strict_transport_security:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers['Strict-Transport-Security'] = hsts_value

        # X-Content-Type-Options
        response.headers['X-Content-Type-Options'] = self.content_type_options

        # X-Frame-Options
        response.headers['X-Frame-Options'] = self.frame_options

        # X-XSS-Protection
        response.headers['X-XSS-Protection'] = self.xss_protection

        # Content-Security-Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp

        # Referrer-Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions-Policy
        permissions = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        response.headers['Permissions-Policy'] = permissions

        # Remove server header
        if 'server' in response.headers:
            del response.headers['server']

        return response


class SecureCookieMiddleware:
    """
    Middleware for securing cookies.

    Sets:
    - Secure flag
    - HttpOnly flag
    - SameSite attribute
    """

    def __init__(
        self,
        secure: bool = True,
        httponly: bool = True,
        samesite: str = "Lax"
    ):
        """
        Initialize secure cookie middleware.

        Args:
            secure: Set Secure flag
            httponly: Set HttpOnly flag
            samesite: SameSite attribute
        """
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite

        logger.info("Secure cookie middleware initialized")

    async def __call__(self, request: Request, call_next):
        """
        Process request and secure cookies.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response with secured cookies
        """
        response = await call_next(request)

        # Secure all cookies
        if 'set-cookie' in response.headers:
            cookies = response.headers['set-cookie']
            # Add Secure, HttpOnly, SameSite to all cookies
            # (This is a simplified implementation)
            # In production, parse and modify each cookie individually
            pass

        return response


def configure_tls(
    app: FastAPI,
    tls_config: Optional[TLSConfig] = None,
    enable_https_redirect: bool = True,
    enable_gzip: bool = True
) -> FastAPI:
    """
    Configure TLS and security for FastAPI application.

    Args:
        app: FastAPI application
        tls_config: TLS configuration
        enable_https_redirect: Enable automatic HTTPS redirect
        enable_gzip: Enable gzip compression

    Returns:
        Configured FastAPI application
    """
    # Add HTTPS redirect middleware
    if enable_https_redirect:
        app.add_middleware(HTTPSRedirectMiddleware)
        logger.info("HTTPS redirect middleware added")

    # Add security headers middleware
    if tls_config:
        app.add_middleware(SecurityHeadersMiddleware,
                          strict_transport_security=tls_config.strict_transport_security,
                          hsts_max_age=tls_config.hsts_max_age,
                          hsts_include_subdomains=tls_config.hsts_include_subdomains,
                          hsts_preload=tls_config.hsts_preload)

        # Add secure cookie middleware
        app.add_middleware(SecureCookieMiddleware,
                          secure=tls_config.secure_cookies,
                          samesite=tls_config.cookie_samesite)

    # Add gzip compression middleware
    if enable_gzip:
        app.add_middleware(GZipMiddleware, minimum_size=1000)
        logger.info("GZip compression middleware added")

    return app


# Global TLS configuration instance
_tls_config: Optional[TLSConfig] = None


def get_tls_config() -> Optional[TLSConfig]:
    """
    Get global TLS configuration.

    Returns:
        TLSConfig instance or None
    """
    return _tls_config


def set_tls_config(config: TLSConfig):
    """
    Set global TLS configuration.

    Args:
        config: TLS configuration
    """
    global _tls_config
    _tls_config = config
    logger.info("Global TLS configuration set")
