"""
sf-permissions: Salesforce Permission Set Analysis Tool

A Python-based tool for analyzing, visualizing, and auditing
Salesforce Permission Sets and Permission Set Groups.

Inspired by PSLab (github.com/OumArbani/PSLab)
"""

__version__ = "1.0.0"
__author__ = "Jag Valaiyapathy"

from .auth import get_sf_connection
