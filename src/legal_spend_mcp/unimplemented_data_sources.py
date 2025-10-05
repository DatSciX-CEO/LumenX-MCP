import logging
from typing import Dict, List, Optional, Any
from datetime import date
from .models import LegalSpendRecord
from .interfaces import DataSourceInterface

logger = logging.getLogger(__name__)


class SimpleLegalDataSource(DataSourceInterface):
    """Data source for the SimpleLegal API."""
    async def get_spend_data(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> List[LegalSpendRecord]:
        logger.warning("SimpleLegalDataSource is not yet implemented.")
        return []

    async def get_vendors(self) -> List[Dict[str, str]]:
        logger.warning("SimpleLegalDataSource is not yet implemented.")
        return []

    async def test_connection(self) -> bool:
        logger.warning("SimpleLegalDataSource is not yet implemented.")
        return False

class BrightflagDataSource(DataSourceInterface):
    """Data source for the Brightflag API."""
    async def get_spend_data(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> List[LegalSpendRecord]:
        logger.warning("BrightflagDataSource is not yet implemented.")
        return []

    async def get_vendors(self) -> List[Dict[str, str]]:
        logger.warning("BrightflagDataSource is not yet implemented.")
        return []

    async def test_connection(self) -> bool:
        logger.warning("BrightflagDataSource is not yet implemented.")
        return False

class TyMetrixDataSource(DataSourceInterface):
    """Data source for the TyMetrix 360 API."""
    async def get_spend_data(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> List[LegalSpendRecord]:
        logger.warning("TyMetrixDataSource is not yet implemented.")
        return []

    async def get_vendors(self) -> List[Dict[str, str]]:
        logger.warning("TyMetrixDataSource is not yet implemented.")
        return []

    async def test_connection(self) -> bool:
        logger.warning("TyMetrixDataSource is not yet implemented.")
        return False

class OnitDataSource(DataSourceInterface):
    """Data source for the Onit API."""
    async def get_spend_data(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> List[LegalSpendRecord]:
        logger.warning("OnitDataSource is not yet implemented.")
        return []

    async def get_vendors(self) -> List[Dict[str, str]]:
        logger.warning("OnitDataSource is not yet implemented.")
        return []

    async def test_connection(self) -> bool:
        logger.warning("OnitDataSource is not yet implemented.")
        return False

class Dynamics365DataSource(DataSourceInterface):
    """Data source for Microsoft Dynamics 365."""
    async def get_spend_data(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> List[LegalSpendRecord]:
        logger.warning("Dynamics365DataSource is not yet implemented.")
        return []

    async def get_vendors(self) -> List[Dict[str, str]]:
        logger.warning("Dynamics365DataSource is not yet implemented.")
        return []

    async def test_connection(self) -> bool:
        logger.warning("Dynamics365DataSource is not yet implemented.")
        return False

class NetSuiteDataSource(DataSourceInterface):
    """Data source for NetSuite."""
    async def get_spend_data(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> List[LegalSpendRecord]:
        logger.warning("NetSuiteDataSource is not yet implemented.")
        return []

    async def get_vendors(self) -> List[Dict[str, str]]:
        logger.warning("NetSuiteDataSource is not yet implemented.")
        return []

    async def test_connection(self) -> bool:
        logger.warning("NetSuiteDataSource is not yet implemented.")
        return False