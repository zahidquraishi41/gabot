from dataclasses import dataclass
from typing import Optional


@dataclass
class Giveaway:
    id: Optional[int]
    guild_id: int
    channel_id: int
    message_id: Optional[int]
    title: str
    prize: str
    criteria: Optional[str]
    winners_count: int
    created_at: int
    ends_at: int
    creator_id: int
    host_id: Optional[int]
    required_role_id: Optional[int]
    ping_role: Optional[int]
    recurring: Optional[int]
    active: int = 1
