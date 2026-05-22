"""Pydantic models for normalized intelligence captures (see architecture §3)."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, HttpUrl
