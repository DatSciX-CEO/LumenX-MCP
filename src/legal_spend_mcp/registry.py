from typing import Dict, Type

class DataSourceRegistry:
    """A registry for data source classes."""
    def __init__(self):
        self._registry: Dict[str, Type] = {}

    def register(self, source_type: str, source_class: Type):
        """Register a data source class."""
        if source_type in self._registry:
            raise ValueError(f"Source type '{source_type}' is already registered.")
        self._registry[source_type] = source_class

    def get_source_class(self, source_type: str) -> Type:
        """Get a data source class by its type name."""
        source_class = self._registry.get(source_type)
        if not source_class:
            raise ValueError(f"No data source registered for type '{source_type}'.")
        return source_class

# Global instance of the registry
registry = DataSourceRegistry()