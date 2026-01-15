"""IDF module for EnergyPlus file handling.

This module provides:
- IDF: Unified class for managing EnergyPlus IDF objects
- IDFBaseModel: Base class for all IDF object models
"""

from src.idf.idf import IDF
from src.idf.models._base import IDFBaseModel

__all__ = ['IDF', 'IDFBaseModel']
