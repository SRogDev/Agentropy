"""Billing schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class CheckoutIn(BaseModel):
    tier: Literal["starter", "pro"]


class CheckoutOut(BaseModel):
    checkout_url: str
    tier: str
