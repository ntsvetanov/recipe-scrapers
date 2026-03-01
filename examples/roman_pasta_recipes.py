#!/usr/bin/env python3
"""
Example: Scrape Roman Pasta Recipes

Demonstrates using the generic :class:`RecipeCollection` framework to download
the four classic Roman pasta dishes (Cacio e Pepe, Carbonara, Amatriciana,
and Gricia) from various supported websites.

To add a new recipe type, copy this file, change the ``RECIPES`` mapping
and the collection name, and you're done.

Usage:
    python examples/roman_pasta_recipes.py
    python examples/roman_pasta_recipes.py --json
    python examples/roman_pasta_recipes.py --dish carbonara
    python examples/roman_pasta_recipes.py --output recipes.json
    python examples/roman_pasta_recipes.py --output recipes.csv --dish gricia

Requirements:
    pip install "recipe-scrapers[online]"
"""

from __future__ import annotations

from examples.recipe_collector import RecipeCollection

# ---------------------------------------------------------------------------
# Recipe URLs by dish  —  just edit this dict to add / remove sources
# ---------------------------------------------------------------------------

RECIPES: dict[str, list[str]] = {
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
# Collection instance  —  this is all that's needed to wire everything up
# ---------------------------------------------------------------------------

roman_pasta = RecipeCollection(name="Roman Pasta", recipes=RECIPES)

if __name__ == "__main__":
    roman_pasta.cli()

