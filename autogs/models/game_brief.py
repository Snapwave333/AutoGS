"""Data models for Stage 1: Trend Scout Bot output."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TrendData:
    """Individual trend data point."""

    keyword: str
    velocity_change: float  # Percentage change
    sentiment_score: float  # -1.0 to 1.0
    volume: int
    source: str  # steam, itch, tiktok, etc.
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketAnalysis:
    """Complete market analysis results."""

    high_demand_keywords: list[str]
    low_supply_keywords: list[str]
    saturated_keywords: list[str]
    rising_trends: list[TrendData]
    competitor_games: list[dict]
    target_audience: str
    estimated_market_size: int
    competition_level: str  # low, medium, high


@dataclass
class GameBrief:
    """
    The output of Stage 1: Trend Scout Bot.
    A concise game concept based on market analysis.
    """

    title: str
    one_liner: str
    genre: str
    sub_genres: list[str]
    player_count: str  # e.g., "1-4 players"
    core_theme: str
    setting: str
    target_platforms: list[str]
    avoid_keywords: list[str]
    target_keywords: list[str]
    market_analysis: Optional[MarketAnalysis] = None
    confidence_score: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "one_liner": self.one_liner,
            "genre": self.genre,
            "sub_genres": self.sub_genres,
            "player_count": self.player_count,
            "core_theme": self.core_theme,
            "setting": self.setting,
            "target_platforms": self.target_platforms,
            "avoid_keywords": self.avoid_keywords,
            "target_keywords": self.target_keywords,
            "confidence_score": self.confidence_score,
            "generated_at": self.generated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameBrief":
        """Create from dictionary."""
        data = data.copy()
        if "generated_at" in data:
            data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        if "market_analysis" in data:
            data.pop("market_analysis")  # Simplified for now
        return cls(**data)

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"""
=== GAME BRIEF ===
Title: {self.title}
Concept: {self.one_liner}
Genre: {self.genre} ({', '.join(self.sub_genres)})
Players: {self.player_count}
Theme: {self.core_theme}
Setting: {self.setting}
Platforms: {', '.join(self.target_platforms)}

Target Keywords: {', '.join(self.target_keywords)}
Avoid Keywords: {', '.join(self.avoid_keywords)}

Confidence Score: {self.confidence_score:.2%}
==================
"""
