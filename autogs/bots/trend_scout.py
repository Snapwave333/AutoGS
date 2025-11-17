"""
Stage 1: Trend Scout Bot
Market research and niche finding through data scraping and analysis.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Any, Optional

from ..core.base_bot import BaseBot
from ..core.config import PipelineConfig
from ..models.game_brief import GameBrief, MarketAnalysis, TrendData


class TrendScoutBot(BaseBot):
    """
    Bot responsible for market research and trend analysis.

    This bot:
    1. Scrapes data from Steam, itch.io, TikTok
    2. Analyzes sentiment and keyword velocity
    3. Identifies high-demand, low-supply niches
    4. Generates a Game Brief with the optimal concept
    """

    # Sample trend data for simulation (real implementation would use APIs)
    TRENDING_GENRES = [
        "survival", "roguelike", "deckbuilder", "metroidvania", "souls-like",
        "farming-sim", "colony-sim", "horror", "cozy", "reverse-bullet-hell"
    ]

    TRENDING_THEMES = [
        "sci-fi", "cosmic-horror", "solarpunk", "post-apocalyptic", "underwater",
        "ancient-ruins", "alternate-history", "biopunk", "dreamscape", "void"
    ]

    TRENDING_MECHANICS = [
        "base-building", "crafting", "automation", "time-loop", "co-op",
        "asymmetric-multiplayer", "procedural-generation", "physics-based",
        "narrative-choice", "town-management"
    ]

    SATURATED_KEYWORDS = [
        "zombies", "battle-royale", "pixel-art-platformer", "match-3",
        "idle-clicker", "generic-fantasy"
    ]

    def run(self, input_data: Optional[Any] = None) -> GameBrief:
        """
        Execute market research and generate a Game Brief.

        Args:
            input_data: Optional constraints or preferences

        Returns:
            GameBrief with the optimal game concept
        """
        self.logger.info("Starting market analysis...")

        # Step 1: Gather trend data
        trends = self._gather_trends()
        self.logger.info(f"Gathered {len(trends)} trend data points")

        # Step 2: Analyze market
        analysis = self._analyze_market(trends)
        self.logger.info(f"Identified {len(analysis.high_demand_keywords)} high-demand keywords")

        # Step 3: Find the gap
        niche = self._find_optimal_niche(analysis)
        self.logger.info(f"Found optimal niche: {niche}")

        # Step 4: Generate Game Brief
        brief = self._generate_game_brief(niche, analysis)
        self.logger.info("Game Brief generated successfully")

        return brief

    def validate_input(self, input_data: Optional[Any]) -> bool:
        """Validate input data. Stage 1 doesn't require input."""
        # Stage 1 can run without input
        return True

    def _gather_trends(self) -> list[TrendData]:
        """
        Gather trend data from various sources.

        In production, this would call:
        - Steam API for wishlists and sales data
        - itch.io scraper for new releases
        - TikTok API for hashtag analysis
        """
        trends = []
        sources = self.config.trend_scout.sources

        # Simulate gathering data from each source
        for source in sources:
            if source == "steam":
                trends.extend(self._scrape_steam())
            elif source == "itch":
                trends.extend(self._scrape_itch())
            elif source == "tiktok":
                trends.extend(self._scrape_tiktok())

        return trends

    def _scrape_steam(self) -> list[TrendData]:
        """Simulate scraping Steam data."""
        self.logger.debug("Scraping Steam trends...")

        # Simulate finding trending keywords
        trends = []
        for keyword in random.sample(self.TRENDING_GENRES + self.TRENDING_THEMES, 10):
            trend = TrendData(
                keyword=keyword,
                velocity_change=random.uniform(1.5, 5.0) * 100,  # 150% to 500%
                sentiment_score=random.uniform(0.6, 0.95),
                volume=random.randint(1000, 50000),
                source="steam"
            )
            trends.append(trend)
        return trends

    def _scrape_itch(self) -> list[TrendData]:
        """Simulate scraping itch.io data."""
        self.logger.debug("Scraping itch.io trends...")

        trends = []
        for keyword in random.sample(self.TRENDING_MECHANICS, 8):
            trend = TrendData(
                keyword=keyword,
                velocity_change=random.uniform(2.0, 8.0) * 100,
                sentiment_score=random.uniform(0.7, 0.98),
                volume=random.randint(500, 20000),
                source="itch"
            )
            trends.append(trend)
        return trends

    def _scrape_tiktok(self) -> list[TrendData]:
        """Simulate scraping TikTok hashtag data."""
        self.logger.debug("Scraping TikTok trends...")

        trends = []
        # TikTok often has niche combinations
        combos = [
            "cozy-horror", "wholesome-roguelike", "chill-survival",
            "narrative-deckbuilder", "co-op-automation"
        ]
        for keyword in combos:
            trend = TrendData(
                keyword=keyword,
                velocity_change=random.uniform(3.0, 10.0) * 100,
                sentiment_score=random.uniform(0.75, 0.99),
                volume=random.randint(10000, 200000),
                source="tiktok"
            )
            trends.append(trend)
        return trends

    def _analyze_market(self, trends: list[TrendData]) -> MarketAnalysis:
        """Analyze gathered trends to identify market opportunities."""

        # Sort by velocity change
        high_velocity = sorted(trends, key=lambda t: t.velocity_change, reverse=True)

        # Identify high-demand keywords (high velocity + positive sentiment)
        high_demand = [
            t.keyword for t in high_velocity
            if t.velocity_change > self.config.trend_scout.velocity_threshold * 100
            and t.sentiment_score > self.config.trend_scout.sentiment_threshold
        ][:15]

        # Simulate finding low-supply keywords (keywords with demand but few releases)
        low_supply = random.sample(self.TRENDING_MECHANICS + self.TRENDING_THEMES, 10)

        # Identify saturated keywords
        saturated = self.SATURATED_KEYWORDS.copy()

        # Get rising trends (top 10 by velocity)
        rising = high_velocity[:10]

        # Simulate competitor analysis
        competitors = [
            {"name": f"Competitor_{i}", "rating": random.uniform(3.5, 4.8)}
            for i in range(5)
        ]

        return MarketAnalysis(
            high_demand_keywords=high_demand,
            low_supply_keywords=low_supply,
            saturated_keywords=saturated,
            rising_trends=rising,
            competitor_games=competitors,
            target_audience="indie gamers aged 18-35",
            estimated_market_size=random.randint(50000, 500000),
            competition_level="low"
        )

    def _find_optimal_niche(self, analysis: MarketAnalysis) -> dict:
        """Find the optimal niche based on market analysis."""

        # Find intersection of high-demand and low-supply
        optimal_keywords = set(analysis.high_demand_keywords) & set(analysis.low_supply_keywords)

        if not optimal_keywords:
            # Use highest demand keyword
            optimal_keywords = set(analysis.high_demand_keywords[:3])

        # Build a niche profile
        niche = {
            "primary_keywords": list(optimal_keywords)[:3],
            "genre": random.choice([
                kw for kw in optimal_keywords
                if kw in self.TRENDING_GENRES
            ] or self.TRENDING_GENRES[:1]),
            "theme": random.choice([
                kw for kw in optimal_keywords
                if kw in self.TRENDING_THEMES
            ] or self.TRENDING_THEMES[:1]),
            "key_mechanics": [
                kw for kw in optimal_keywords
                if kw in self.TRENDING_MECHANICS
            ] or random.sample(self.TRENDING_MECHANICS, 2),
            "avoid": analysis.saturated_keywords[:5]
        }

        return niche

    def _generate_game_brief(self, niche: dict, analysis: MarketAnalysis) -> GameBrief:
        """Generate a complete Game Brief based on the niche analysis."""

        # Build the one-liner concept
        genre = niche.get("genre", ["survival"])[0] if isinstance(niche.get("genre"), list) else niche.get("genre", "survival")
        theme = niche.get("theme", ["sci-fi"])[0] if isinstance(niche.get("theme"), list) else niche.get("theme", "sci-fi")
        mechanics = niche.get("key_mechanics", ["base-building", "co-op"])

        # Generate title
        title_parts = [
            theme.replace("-", " ").title(),
            genre.replace("-", " ").title(),
            random.choice(["Chronicles", "Station", "Protocol", "Frontier", "Nexus"])
        ]
        title = " ".join(random.sample(title_parts, 2))

        # Generate one-liner
        mechanics_str = " and ".join(mechanics[:2]).replace("-", " ")
        one_liner = (
            f"A {' '.join(niche['primary_keywords'][:2]).replace('-', ' ')} game "
            f"featuring {mechanics_str} mechanics in a {theme.replace('-', ' ')} setting"
        )

        # Determine player count based on mechanics
        if "co-op" in mechanics or "multiplayer" in " ".join(mechanics):
            player_count = "1-4 players"
        else:
            player_count = "1 player"

        # Create the Game Brief
        brief = GameBrief(
            title=title,
            one_liner=one_liner,
            genre=genre,
            sub_genres=niche["primary_keywords"][:3],
            player_count=player_count,
            core_theme=theme,
            setting=f"{theme.replace('-', ' ').title()} environment with {genre} elements",
            target_platforms=["PC", "Steam"],
            avoid_keywords=niche["avoid"],
            target_keywords=niche["primary_keywords"] + mechanics,
            market_analysis=analysis,
            confidence_score=random.uniform(0.75, 0.95)
        )

        return brief

    def _dry_run(self, input_data: Optional[Any]) -> GameBrief:
        """Simulate execution with sample data."""
        self.logger.info("DRY RUN: Generating sample Game Brief")

        return GameBrief(
            title="Void Station Protocol",
            one_liner="A 1-4 player co-op sci-fi survival game with base-building and automation mechanics",
            genre="survival",
            sub_genres=["sci-fi", "co-op", "base-building"],
            player_count="1-4 players",
            core_theme="sci-fi",
            setting="Abandoned space station on the edge of known space",
            target_platforms=["PC", "Steam"],
            avoid_keywords=["zombies", "pixel-art", "battle-royale"],
            target_keywords=["co-op", "sci-fi", "survival", "base-building", "automation"],
            confidence_score=0.87
        )
