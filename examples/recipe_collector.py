#!/usr/bin/env python3
"""
Generic Recipe Collector Framework

Provides reusable components for scraping, storing, and displaying recipes
from supported websites.  Recipe collections are defined as simple
``dict[str, list[str]]`` mappings of dish names to URLs and can be scraped
with a single function call.

Creating a new collection
-------------------------

.. code-block:: python

    from examples.recipe_collector import RecipeCollection

    THAI_CURRIES = RecipeCollection(
        name="Thai Curries",
        recipes={
            "green_curry": [
                "https://www.allrecipes.com/recipe/...",
            ],
            "massaman": [
                "https://www.bonappetit.com/recipe/...",
            ],
        },
    )

    if __name__ == "__main__":
        THAI_CURRIES.cli()
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from recipe_scrapers import scrape_me

# ---------------------------------------------------------------------------
# Generic recipe data model
# ---------------------------------------------------------------------------


@dataclass
class RecipeData:
    """Generic, structured format for storing a scraped recipe."""

    title: str
    url: str
    dish: str = ""
    source: str = ""
    author: str | None = None
    total_time: int | None = None
    cook_time: int | None = None
    prep_time: int | None = None
    yields: str | None = None
    category: str | None = None
    cuisine: str | None = None
    image: str | None = None
    ingredients: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    nutrients: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary representation."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def save_to_json(recipes: list[RecipeData], path: str | Path) -> None:
    """Save recipes to a JSON file."""
    data = [r.to_dict() for r in recipes]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_from_json(path: str | Path) -> list[RecipeData]:
    """Load recipes from a JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [RecipeData(**item) for item in data]


def save_to_csv(recipes: list[RecipeData], path: str | Path) -> None:
    """Save recipes to a CSV file.

    List and dict fields are stored as JSON strings so that the CSV
    remains a flat table while preserving all data.
    """
    fieldnames = list(RecipeData.__dataclass_fields__.keys())
    if not recipes:
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for recipe in recipes:
            row = recipe.to_dict()
            for key in ("ingredients", "instructions", "nutrients"):
                row[key] = json.dumps(row[key], ensure_ascii=False)
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Scraping helpers
# ---------------------------------------------------------------------------


def _safe_call(func):
    """Call a scraper method, returning None on failure."""
    try:
        return func()
    except Exception:
        return None


def scrape_recipe(url: str, dish: str = "") -> RecipeData | None:
    """
    Scrape a single recipe URL and return a :class:`RecipeData` object.

    Returns ``None`` if scraping fails.
    """
    try:
        scraper = scrape_me(url)
        return RecipeData(
            title=scraper.title(),
            url=url,
            dish=dish,
            source=_safe_call(scraper.site_name) or "",
            author=_safe_call(scraper.author),
            total_time=_safe_call(scraper.total_time),
            cook_time=_safe_call(scraper.cook_time),
            prep_time=_safe_call(scraper.prep_time),
            yields=_safe_call(scraper.yields),
            category=_safe_call(scraper.category),
            cuisine=_safe_call(scraper.cuisine),
            image=_safe_call(scraper.image),
            ingredients=scraper.ingredients(),
            instructions=scraper.instructions_list(),
            nutrients=_safe_call(scraper.nutrients) or {},
        )
    except Exception as e:
        print(f"  [!] Failed to scrape {url}: {e}", file=sys.stderr)
        return None


def print_recipe(recipe: RecipeData) -> None:
    """Print a recipe in a human-readable format."""
    print(f"\n  Title:      {recipe.title}")
    print(f"  URL:        {recipe.url}")
    if recipe.source:
        print(f"  Source:     {recipe.source}")
    if recipe.author:
        print(f"  Author:     {recipe.author}")
    if recipe.total_time:
        print(f"  Total Time: {recipe.total_time} min")
    if recipe.yields:
        print(f"  Yields:     {recipe.yields}")
    if recipe.cuisine:
        print(f"  Cuisine:    {recipe.cuisine}")
    print(f"  Ingredients ({len(recipe.ingredients)}):")
    for ing in recipe.ingredients:
        print(f"    - {ing}")
    print(f"  Steps ({len(recipe.instructions)}):")
    for i, step in enumerate(recipe.instructions, 1):
        print(f"    {i}. {step}")


# ---------------------------------------------------------------------------
# Recipe collection
# ---------------------------------------------------------------------------


@dataclass
class RecipeCollection:
    """A named collection of dish → URL mappings.

    Encapsulates scraping, display, storage and CLI generation so that
    adding a new recipe type only requires defining a name and a mapping.

    Example
    -------
    >>> col = RecipeCollection("My Recipes", {"dish_a": ["https://..."]})
    >>> col.scrape(dishes=["dish_a"], output="recipes.json")
    """

    name: str
    recipes: dict[str, list[str]]

    # -- public API ----------------------------------------------------------

    @property
    def dish_names(self) -> list[str]:
        """Return a sorted list of available dish names."""
        return sorted(self.recipes.keys())

    def scrape(
        self,
        dishes: list[str] | None = None,
        output: str | None = None,
    ) -> list[RecipeData]:
        """Scrape recipes for the given *dishes* (default: all).

        Parameters
        ----------
        dishes:
            Dish keys to scrape.  ``None`` means all dishes in the collection.
        output:
            Optional file path (``.json`` or ``.csv``).  When set the results
            are saved to the file instead of being printed.

        Returns
        -------
        list[RecipeData]
        """
        if dishes is None:
            dishes = list(self.recipes.keys())

        all_recipes: list[RecipeData] = []

        for dish in dishes:
            urls = self.recipes.get(dish)
            if urls is None:
                available = ", ".join(self.recipes.keys())
                print(
                    f"Unknown dish '{dish}'. Available: {available}",
                    file=sys.stderr,
                )
                continue

            if output is None:
                print(f"\n{'=' * 60}")
                print(f"  {dish.replace('_', ' ').title()}")
                print(f"{'=' * 60}")

            for url in urls:
                recipe = scrape_recipe(url, dish=dish)
                if recipe is not None:
                    all_recipes.append(recipe)
                    if output is None:
                        print_recipe(recipe)

        if output is not None:
            path = Path(output)
            if path.suffix == ".csv":
                save_to_csv(all_recipes, path)
            else:
                save_to_json(all_recipes, path)
            print(f"Saved {len(all_recipes)} recipes to {path}")

        return all_recipes

    # -- CLI helper ----------------------------------------------------------

    def cli(self, args: list[str] | None = None) -> None:
        """Run an ``argparse``-based CLI for this collection."""
        parser = argparse.ArgumentParser(
            description=f"Scrape {self.name} recipes from supported websites.",
        )
        parser.add_argument(
            "--output", "-o",
            help="Save results to a file (.json or .csv)",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print results as JSON to stdout (ignored when --output is set)",
        )
        parser.add_argument(
            "--dish",
            choices=self.dish_names,
            action="append",
            dest="dishes",
            help="Scrape only a specific dish (can be repeated)",
        )
        parsed = parser.parse_args(args)

        if parsed.json and not parsed.output:
            recipes = self.scrape(dishes=parsed.dishes, output=None)
            data = [r.to_dict() for r in recipes]
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            self.scrape(dishes=parsed.dishes, output=parsed.output)
