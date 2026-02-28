#!/usr/bin/env python3
"""
Example: Scrape Roman Pasta Recipes

Demonstrates using recipe-scrapers to download the four classic Roman pasta
recipes (Cacio e Pepe, Carbonara, Amatriciana, and Gricia) from various
supported websites.

Usage:
    python examples/roman_pasta_recipes.py
    python examples/roman_pasta_recipes.py --json          # output as JSON
    python examples/roman_pasta_recipes.py --dish carbonara # scrape one dish

Requirements:
    pip install "recipe-scrapers[online]"
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from recipe_scrapers import scrape_me

# Curated list of Roman pasta recipe URLs from supported websites.
# Each entry maps a dish name to a list of recipe URLs on supported sites.
ROMAN_PASTA_RECIPES: dict[str, list[str]] = {
    "cacio_e_pepe": [
        "https://www.allrecipes.com/recipe/257874/cacio-e-pepe/",
        "https://www.bonappetit.com/recipe/cacio-e-pepe",
        "https://www.simplyrecipes.com/recipes/cacio_e_pepe/",
    ],
    "carbonara": [
        "https://www.allrecipes.com/recipe/11973/spaghetti-carbonara-ii/",
        "https://www.bonappetit.com/recipe/simple-carbonara",
        "https://www.simplyrecipes.com/recipes/pasta_carbonara/",
    ],
    "amatriciana": [
        "https://www.allrecipes.com/recipe/222015/bucatini-allamatriciana/",
        "https://www.bonappetit.com/recipe/amatriciana",
        "https://www.simplyrecipes.com/recipes/pasta_allamatriciana/",
    ],
    "gricia": [
        "https://www.bonappetit.com/recipe/pasta-alla-gricia",
        "https://www.seriouseats.com/pasta-alla-gricia-recipe",
    ],
}


def scrape_recipe(url: str) -> dict[str, Any] | None:
    """
    Scrape a single recipe URL and return a dictionary of recipe data.

    Returns None if scraping fails.
    """
    try:
        scraper = scrape_me(url)
        return {
            "title": scraper.title(),
            "url": url,
            "author": _safe_call(scraper.author),
            "total_time": _safe_call(scraper.total_time),
            "yields": _safe_call(scraper.yields),
            "ingredients": scraper.ingredients(),
            "instructions": scraper.instructions_list(),
        }
    except Exception as e:
        print(f"  [!] Failed to scrape {url}: {e}", file=sys.stderr)
        return None


def _safe_call(func):
    """Call a scraper method, returning None on failure."""
    try:
        return func()
    except Exception:
        return None


def print_recipe(recipe: dict[str, Any]) -> None:
    """Print a recipe in a human-readable format."""
    print(f"\n  Title:      {recipe['title']}")
    print(f"  URL:        {recipe['url']}")
    if recipe.get("author"):
        print(f"  Author:     {recipe['author']}")
    if recipe.get("total_time"):
        print(f"  Total Time: {recipe['total_time']} min")
    if recipe.get("yields"):
        print(f"  Yields:     {recipe['yields']}")
    print(f"  Ingredients ({len(recipe['ingredients'])}):")
    for ing in recipe["ingredients"]:
        print(f"    - {ing}")
    print(f"  Steps ({len(recipe['instructions'])}):")
    for i, step in enumerate(recipe["instructions"], 1):
        print(f"    {i}. {step}")


def scrape_roman_recipes(
    dishes: list[str] | None = None,
    as_json: bool = False,
) -> list[dict[str, Any]]:
    """
    Scrape Roman pasta recipes for the specified dishes.

    Parameters
    ----------
    dishes : list[str] | None
        Which dishes to scrape. If None, scrape all four Roman pasta dishes.
    as_json : bool
        If True, output results as JSON instead of human-readable text.

    Returns
    -------
    list[dict[str, Any]]
        A list of successfully scraped recipe dictionaries.
    """
    if dishes is None:
        dishes = list(ROMAN_PASTA_RECIPES.keys())

    all_recipes: list[dict[str, Any]] = []

    for dish in dishes:
        urls = ROMAN_PASTA_RECIPES.get(dish)
        if urls is None:
            available = ", ".join(ROMAN_PASTA_RECIPES.keys())
            print(
                f"Unknown dish '{dish}'. Available: {available}",
                file=sys.stderr,
            )
            continue

        if not as_json:
            print(f"\n{'=' * 60}")
            print(f"  {dish.replace('_', ' ').title()}")
            print(f"{'=' * 60}")

        for url in urls:
            recipe = scrape_recipe(url)
            if recipe is not None:
                recipe["dish"] = dish
                all_recipes.append(recipe)
                if not as_json:
                    print_recipe(recipe)

    if as_json:
        print(json.dumps(all_recipes, indent=2, ensure_ascii=False))

    return all_recipes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape Roman pasta recipes from supported websites."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--dish",
        choices=list(ROMAN_PASTA_RECIPES.keys()),
        action="append",
        dest="dishes",
        help="Scrape only a specific dish (can be repeated)",
    )
    args = parser.parse_args()

    scrape_roman_recipes(dishes=args.dishes, as_json=args.json)


if __name__ == "__main__":
    main()
