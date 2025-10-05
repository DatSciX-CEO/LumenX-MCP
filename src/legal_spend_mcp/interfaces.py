from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import date
from .config import DataSourceConfig
from .registry import registry

class DataSourceInterface(ABC):
    """Abstract base class for data sources following MCP patterns."""

    def __init__(self, config: "DataSourceConfig"):
        self.config = config

    def __init_subclass__(cls, **kwargs):
        """Automatically register data source subclasses."""
        super().__init_subclass__(**kwargs)

        # Use a specific registration key if provided, otherwise generate one
        source_key = getattr(cls, 'registration_key', None)
        if not source_key:
            source_key = cls.__name__.replace("DataSource", "").lower()

        # Do not register the base interface itself
        if "interface" not in source_key:
            registry.register(source_key, cls)

    @abstractmethod
    async def get_spend_data(
        self,
        start_date: date,
        end_date: date,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List["LegalSpendRecord"]:
        """Retrieve spend data for a given period."""
        pass

    @abstractmethod
    async def get_vendors(self) -> List[Dict[str, str]]:
        """Get list of all vendors."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if data source is accessible."""
        pass