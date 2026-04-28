"""
sf-ai-agentforce-observability: Agentforce Session Tracing Extraction & Analysis

This package provides tools to extract and analyze Agentforce session tracing
data from Salesforce Data Cloud.

Modules:
    auth: JWT Bearer authentication for Data Cloud API
    datacloud_client: Data Cloud Query API client with pagination
    extractor: STDM (Session Tracing Data Model) extraction orchestrator
    models: Pydantic models and PyArrow schemas for STDM data
    analyzer: Polars-based analysis helpers
    cli: Command-line interface
"""

__version__ = "1.0.0"
__author__ = "Jag Valaiyapathy"
