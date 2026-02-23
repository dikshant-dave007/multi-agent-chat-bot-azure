"""
Semantic Kernel factory for AI orchestration.

This module provides factory functions to create and configure Semantic Kernel
instances with Azure OpenAI integration.
"""

from typing import Optional
import httpx

from azure.identity import DefaultAzureCredential
from openai import AsyncAzureOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from src.core.config import get_settings
from src.core.exceptions import InitializationError
from src.core.logging_config import LoggerMixin


class SemanticKernelFactory(LoggerMixin):
    """
    Factory for creating configured Semantic Kernel instances.

    This factory handles:
    - Kernel initialization
    - Azure OpenAI connection setup
    - Plugin registration
    - Service configuration
    """

    def __init__(self):
        """Initialize the Semantic Kernel factory."""
        self.settings = get_settings()
        self._kernel: Optional[Kernel] = None

    def create_kernel(self, service_id: Optional[str] = None) -> Kernel:
        """
        Create a new configured Kernel instance.

        Args:
            service_id: Optional service ID for the AI service

        Returns:
            Kernel: Configured Semantic Kernel instance

        Raises:
            InitializationError: If kernel creation fails
        """
        try:
            self.logger.info("creating_semantic_kernel", service_id=service_id)

            # Create kernel
            kernel = Kernel()

            # Add Azure OpenAI chat completion service
            service_id = service_id or "azure_openai_chat"
            kernel.add_service(self._create_azure_chat_service(service_id))

            self.logger.info("semantic_kernel_created", service_id=service_id)
            return kernel

        except Exception as e:
            self.logger.error("failed_to_create_kernel", error=str(e), exc_info=True)
            raise InitializationError(
                message="Failed to create Semantic Kernel",
                details={"error": str(e)},
            ) from e

    def _create_azure_chat_service(self, service_id: str) -> AzureChatCompletion:
        """
        Create Azure OpenAI chat completion service.

        Args:
            service_id: Service identifier

        Returns:
            AzureChatCompletion: Configured chat service

        Raises:
            InitializationError: If service creation fails
        """
        try:
            openai_settings = self.settings.azure_openai

            # Create custom httpx client to avoid the 'proxies' parameter issue
            # This is needed because newer versions of openai package don't support
            # the 'proxies' parameter that semantic-kernel tries to pass
            http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
                follow_redirects=True,
            )

            # Determine authentication method
            if openai_settings.api_key:
                # Use API key authentication
                self.logger.debug("using_api_key_authentication")
                
                # Create custom Azure OpenAI client
                async_client = AsyncAzureOpenAI(
                    azure_endpoint=openai_settings.endpoint,
                    api_key=openai_settings.api_key,
                    api_version=openai_settings.api_version,
                    http_client=http_client,
                )
                
                # Create chat completion service with custom client
                service = AzureChatCompletion(
                    service_id=service_id,
                    deployment_name=openai_settings.deployment_name,
                    async_client=async_client,
                )
            else:
                # Use managed identity
                self.logger.debug("using_managed_identity_authentication")
                credential = DefaultAzureCredential()
                
                # Get token for Azure OpenAI
                token = credential.get_token("https://cognitiveservices.azure.com/.default")
                
                # Create custom Azure OpenAI client with token
                async_client = AsyncAzureOpenAI(
                    azure_endpoint=openai_settings.endpoint,
                    azure_ad_token=token.token,
                    api_version=openai_settings.api_version,
                    http_client=http_client,
                )
                
                # Create chat completion service with custom client
                service = AzureChatCompletion(
                    service_id=service_id,
                    deployment_name=openai_settings.deployment_name,
                    async_client=async_client,
                )

            self.logger.info(
                "azure_chat_service_created",
                service_id=service_id,
                deployment=openai_settings.deployment_name,
                endpoint=openai_settings.endpoint,
            )

            return service

        except Exception as e:
            self.logger.error("failed_to_create_chat_service", error=str(e), exc_info=True)
            raise InitializationError(
                message="Failed to create Azure Chat service",
                details={"error": str(e), "service_id": service_id},
            ) from e

    def get_or_create_kernel(self) -> Kernel:
        """
        Get cached kernel instance or create new one.

        Returns:
            Kernel: Semantic Kernel instance
        """
        if self._kernel is None:
            self._kernel = self.create_kernel()
        return self._kernel

    def reset_kernel(self) -> None:
        """Reset the cached kernel instance."""
        self._kernel = None
        self.logger.info("kernel_cache_reset")


# Global factory instance
_kernel_factory: Optional[SemanticKernelFactory] = None


def get_kernel_factory() -> SemanticKernelFactory:
    """
    Get the global Semantic Kernel factory instance.

    Returns:
        SemanticKernelFactory: Factory instance
    """
    global _kernel_factory
    if _kernel_factory is None:
        _kernel_factory = SemanticKernelFactory()
    return _kernel_factory


def create_kernel(service_id: Optional[str] = None) -> Kernel:
    """
    Create a new Semantic Kernel instance.

    Args:
        service_id: Optional service ID

    Returns:
        Kernel: Configured kernel instance
    """
    factory = get_kernel_factory()
    return factory.create_kernel(service_id=service_id)


def get_kernel() -> Kernel:
    """
    Get cached Semantic Kernel instance or create new one.

    Returns:
        Kernel: Kernel instance
    """
    factory = get_kernel_factory()
    return factory.get_or_create_kernel()
