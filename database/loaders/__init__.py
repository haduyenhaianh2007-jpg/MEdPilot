"""
Data loaders - Load diseases from files and index to vector database
"""
from .load_and_index_diseases import DiseaseIndexer
from .load_and_index_optimized_combined import DiseaseIndexerCombined

__all__ = ["DiseaseIndexer", "DiseaseIndexerCombined"]
