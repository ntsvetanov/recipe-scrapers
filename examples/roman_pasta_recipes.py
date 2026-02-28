#!/usr/bin/env python3
"""
Example: Scrape Roman Pasta Recipes

Demonstrates using recipe-scrapers to download the four classic Roman pasta
recipes (Cacio e Pepe, Carbonara, Amatriciana, and Gricia) from various
supported websites, and store them in a generic format (JSON or CSV).

Usage:
    python examples/roman_pasta_recipes.py
    python examples/roman_pasta_recipes.py --json
    python examples/roman_pasta_recipes.py --dish carbonara
    python examples/roman_pasta_recipes.py --output recipes.json
    python examples/roman_pasta_recipes.py --output recipes.csv
    python examples/roman_pasta_recipes.py --output recipes.json --dish gricia

Requirements:
    pip install "recipe-scrapers[online]"
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
# Curated Roman pasta recipe URLs from supported websites
# ---------------------------------------------------------------------------

ROMAN_PASTA_RECIPES: dict[str, list[str]] = {
    "cacio_e_pepe": [
        "https://www.allrecipes.com/recipe/257874/cacio-e-pepe/",
        "https://www.bonappetit.com/recipe/cacio-e-pepe",
        "https://www.simplyrecipes.com/recipes/cacio_e_pepe/",
        "https://www.seriouseats.com/cacio-e-pepe-recipe",
        "https://www.jamieoliver.com/recipes/pasta-recipes/gennaro-s-cacio-e-pepe/",
        "https://www.bbcgoodfood.com/recipes/cacio-e-pepe",
        "https://ricette.giallozafferano.it/Cacio-e-pepe.html",
        "https://www.epicurious.com/recipes/food/views/cacio-e-pepe",
        "https://food52.com/recipes/37837-cacio-e-pepe",
        "https://thekitchn.com/cacio-e-pepe-recipe-23678086",
    ],
    "carbonara": [
        "https://www.allrecipes.com/recipe/11973/spaghetti-carbonara-ii/",
        "https://www.bonappetit.com/recipe/simple-carbonara",
        "https://www.simplyrecipes.com/recipes/pasta_carbonara/",
        "https://www.seriouseats.com/pasta-carbonara-sauce-recipe",
        "https://www.jamieoliver.com/recipes/pasta-recipes/gennaro-s-classic-spaghetti-carbonara/",
        "https://www.bbcgoodfood.com/recipes/ultimate-spaghetti-carbonara-recipe",
        "https://ricette.giallozafferano.it/Spaghetti-alla-Carbonara.html",
        "https://www.epicurious.com/recipes/food/views/spaghetti-carbonara",
        "https://food52.com/recipes/25749-pasta-carbonara",
        "https://www.foodnetwork.com/recipes/tyler-florence/spaghetti-alla-carbonara-recipe-1914141",
    ],
    "amatriciana": [
        "https://www.allrecipes.com/recipe/222015/bucatini-allamatriciana/",
        "https://www.bonappetit.com/recipe/amatriciana",
        "https://www.simplyrecipes.com/recipes/pasta_allamatriciana/",
        "https://www.seriouseats.com/bucatini-all-amatriciana-recipe",
        "https://www.jamieoliver.com/recipes/pasta-recipes/amatriciana-sauce/",
        "https://www.bbcgoodfood.com/recipes/amatriciana",
        "https://ricette.giallozafferano.it/Bucatini-all-amatriciana.html",
        "https://www.epicurious.com/recipes/food/views/bucatini-all-amatriciana",
        "https://food52.com/recipes/18498-bucatini-all-amatriciana",
        "https://www.foodnetwork.com/recipes/anne-burrell/bucatini-all-amatriciana-recipe-1942854",
    ],
    "gricia": [
        "https://www.bonappetit.com/recipe/pasta-alla-gricia",
        "https://www.seriouseats.com/pasta-alla-gricia-recipe",
        "https://www.bbcgoodfood.com/recipes/pasta-alla-gricia",
        "https://ricette.giallozafferano.it/Pasta-alla-gricia.html",
        "https://food52.com/recipes/80148-pasta-alla-gricia",
        "https://thekitchn.com/pasta-alla-gricia-recipe-23304869",
    ],
}


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
    Scrape a single recipe URL and return a RecipeData object.

    Returns None if scraping fails.
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


def scrape_roman_recipes(
    dishes: list[str] | None = None,
    output: str | None = None,
) -> list[RecipeData]:
    """
    Scrape Roman pasta recipes for the specified dishes.

    Parameters
    ----------
    dishes : list[str] | None
        Which dishes to scrape. If None, scrape all four Roman pasta dishes.
    output : str | None
        Optional file path to save results. Supports ``.json`` and ``.csv``.
        If None, prints results to stdout.

    Returns
    -------
    list[RecipeData]
        A list of successfully scraped recipes.
    """
    if dishes is None:
        dishes = list(ROMAN_PASTA_RECIPES.keys())

    all_recipes: list[RecipeData] = []

    for dish in dishes:
        urls = ROMAN_PASTA_RECIPES.get(dish)
        if urls is None:
            available = ", ".join(ROMAN_PASTA_RECIPES.keys())
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape Roman pasta recipes from supported websites."
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
        choices=list(ROMAN_PASTA_RECIPES.keys()),
        action="append",
        dest="dishes",
        help="Scrape only a specific dish (can be repeated)",
    )
    args = parser.parse_args()

    if args.json and not args.output:
        recipes = scrape_roman_recipes(dishes=args.dishes, output=None)
        data = [r.to_dict() for r in recipes]
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        scrape_roman_recipes(dishes=args.dishes, output=args.output)


if __name__ == "__main__":
    main()
