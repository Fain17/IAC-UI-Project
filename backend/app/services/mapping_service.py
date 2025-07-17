from app.db.repositories import ConfigMappingRepository
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

async def load_mappings() -> Dict[str, str]:
    """Load mappings from the database."""
    return await ConfigMappingRepository.get_all()

async def create_mapping(instance_name: str, lt_name: str) -> bool:
    """
    Create a new mapping and save to the database.
    Returns True if created, False if mapping already exists.
    """
    return await ConfigMappingRepository.create(instance_name, lt_name)

async def update_mapping(instance_name: str, lt_name: str) -> bool:
    """
    Update an existing mapping and save to the database.
    Returns True if updated, False if mapping does not exist.
    """
    return await ConfigMappingRepository.update(instance_name, lt_name)

async def get_all_mappings() -> Dict[str, str]:
    """Get all mappings from the database."""
    return await ConfigMappingRepository.get_all()

async def delete_mapping(instance_name: str) -> bool:
    """Delete a mapping by instance name from the database. Returns True if deleted."""
    return await ConfigMappingRepository.delete(instance_name)

async def get_mapping_by_instance(instance_name: str) -> Optional[str]:
    """Get launch template name for a specific instance."""
    return await ConfigMappingRepository.get_by_instance(instance_name) 