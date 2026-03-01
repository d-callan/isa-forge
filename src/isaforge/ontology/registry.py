"""Registry for ontology services."""

from isaforge.ontology.base import BaseOntologyService
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


class OntologyRegistry:
    """Registry for managing ontology service instances."""

    _services: dict[str, BaseOntologyService] = {}
    _default_service: str | None = None

    @classmethod
    def register(cls, name: str, service: BaseOntologyService) -> None:
        """Register an ontology service.

        Args:
            name: Name to register the service under.
            service: The ontology service instance.
        """
        cls._services[name] = service
        logger.debug("ontology_service_registered", name=name)

        # Set first registered service as default
        if cls._default_service is None:
            cls._default_service = name

    @classmethod
    def get(cls, name: str) -> BaseOntologyService | None:
        """Get an ontology service by name.

        Args:
            name: Name of the service.

        Returns:
            The ontology service, or None if not found.
        """
        return cls._services.get(name)

    @classmethod
    def get_default(cls) -> BaseOntologyService | None:
        """Get the default ontology service.

        Returns:
            The default ontology service, or None if none registered.
        """
        if cls._default_service:
            return cls._services.get(cls._default_service)
        return None

    @classmethod
    def set_default(cls, name: str) -> None:
        """Set the default ontology service.

        Args:
            name: Name of the service to set as default.

        Raises:
            ValueError: If the service is not registered.
        """
        if name not in cls._services:
            raise ValueError(f"Service not registered: {name}")
        cls._default_service = name

    @classmethod
    def list_services(cls) -> list[str]:
        """List all registered service names.

        Returns:
            List of service names.
        """
        return list(cls._services.keys())

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister an ontology service.

        Args:
            name: Name of the service to unregister.
        """
        if name in cls._services:
            del cls._services[name]
            if cls._default_service == name:
                cls._default_service = next(iter(cls._services), None)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services."""
        cls._services.clear()
        cls._default_service = None


def setup_default_services() -> None:
    """Set up the default ontology services."""
    from isaforge.ontology.services.ols import OLSService
    from isaforge.ontology.services.zooma import ZoomaService

    # Register OLS as primary service
    OntologyRegistry.register("ols", OLSService())

    # Register Zooma as secondary service
    OntologyRegistry.register("zooma", ZoomaService())

    # OLS is the default
    OntologyRegistry.set_default("ols")

    logger.info("default_ontology_services_configured")
