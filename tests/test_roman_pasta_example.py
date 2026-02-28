import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from examples.roman_pasta_recipes import (
    ROMAN_PASTA_RECIPES,
    RecipeData,
    scrape_recipe,
    scrape_roman_recipes,
    save_to_json,
    load_from_json,
    save_to_csv,
    _safe_call,
)


class TestRomanPastaRecipes(unittest.TestCase):
    """Tests for the Roman pasta recipes example script."""

    def test_all_four_roman_dishes_defined(self):
        """All four classic Roman pasta dishes should be present."""
        expected = {"cacio_e_pepe", "carbonara", "amatriciana", "gricia"}
        self.assertEqual(set(ROMAN_PASTA_RECIPES.keys()), expected)

    def test_each_dish_has_urls(self):
        """Each dish should have at least one recipe URL."""
        for dish, urls in ROMAN_PASTA_RECIPES.items():
            with self.subTest(dish=dish):
                self.assertGreater(len(urls), 0)

    def test_all_urls_are_strings(self):
        """Every URL should be a non-empty string starting with https."""
        for dish, urls in ROMAN_PASTA_RECIPES.items():
            for url in urls:
                with self.subTest(url=url):
                    self.assertIsInstance(url, str)
                    self.assertTrue(url.startswith("https://"))

    def test_multiple_sources_per_dish(self):
        """Each dish should have URLs from multiple sources."""
        for dish, urls in ROMAN_PASTA_RECIPES.items():
            with self.subTest(dish=dish):
                self.assertGreaterEqual(len(urls), 5)

    def test_safe_call_returns_value(self):
        """_safe_call should return the function result on success."""
        self.assertEqual(_safe_call(lambda: 42), 42)

    def test_safe_call_returns_none_on_error(self):
        """_safe_call should return None when the function raises."""

        def failing():
            raise ValueError("boom")

        self.assertIsNone(_safe_call(failing))


class TestRecipeData(unittest.TestCase):
    """Tests for the RecipeData dataclass."""

    def _sample_recipe(self, **overrides):
        defaults = {
            "title": "Cacio e Pepe",
            "url": "https://example.com/recipe",
            "dish": "cacio_e_pepe",
            "source": "Example Site",
            "author": "Chef Test",
            "total_time": 30,
            "cook_time": 15,
            "prep_time": 15,
            "yields": "4 servings",
            "category": "Pasta",
            "cuisine": "Italian",
            "image": "https://example.com/image.jpg",
            "ingredients": ["pasta", "pecorino", "pepper"],
            "instructions": ["Boil pasta", "Add cheese"],
            "nutrients": {"calories": "400"},
        }
        defaults.update(overrides)
        return RecipeData(**defaults)

    def test_to_dict_round_trip(self):
        """to_dict should produce a dict that can recreate the object."""
        recipe = self._sample_recipe()
        d = recipe.to_dict()
        self.assertEqual(d["title"], "Cacio e Pepe")
        self.assertEqual(d["ingredients"], ["pasta", "pecorino", "pepper"])
        restored = RecipeData(**d)
        self.assertEqual(restored, recipe)

    def test_defaults(self):
        """RecipeData should have sensible defaults for optional fields."""
        recipe = RecipeData(title="Test", url="https://example.com")
        self.assertEqual(recipe.dish, "")
        self.assertIsNone(recipe.author)
        self.assertEqual(recipe.ingredients, [])
        self.assertEqual(recipe.nutrients, {})


class TestStorage(unittest.TestCase):
    """Tests for JSON and CSV storage helpers."""

    def _sample_recipes(self):
        return [
            RecipeData(
                title="Cacio e Pepe",
                url="https://example.com/1",
                dish="cacio_e_pepe",
                source="Example",
                ingredients=["pasta", "pecorino"],
                instructions=["Boil", "Mix"],
                nutrients={"calories": "400"},
            ),
            RecipeData(
                title="Carbonara",
                url="https://example.com/2",
                dish="carbonara",
                source="Example",
                ingredients=["pasta", "guanciale", "egg"],
                instructions=["Fry", "Toss"],
            ),
        ]

    def test_save_and_load_json(self):
        """Recipes saved to JSON should round-trip back correctly."""
        recipes = self._sample_recipes()
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            path = f.name
        try:
            save_to_json(recipes, path)
            loaded = load_from_json(path)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0].title, "Cacio e Pepe")
            self.assertEqual(loaded[1].ingredients, ["pasta", "guanciale", "egg"])
        finally:
            os.unlink(path)

    def test_save_csv(self):
        """Recipes saved to CSV should produce a valid file."""
        recipes = self._sample_recipes()
        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False, mode="w"
        ) as f:
            path = f.name
        try:
            save_to_csv(recipes, path)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Cacio e Pepe", content)
            self.assertIn("Carbonara", content)
            # list fields should be serialised as JSON strings
            self.assertIn('"pasta"', content)
        finally:
            os.unlink(path)

    def test_save_csv_empty(self):
        """save_to_csv with empty list should not create content."""
        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False, mode="w"
        ) as f:
            path = f.name
        try:
            save_to_csv([], path)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "")
        finally:
            os.unlink(path)


class TestScraping(unittest.TestCase):
    """Tests for scraping functions."""

    @patch("examples.roman_pasta_recipes.scrape_me")
    def test_scrape_recipe_success(self, mock_scrape_me):
        """scrape_recipe should return a RecipeData on success."""
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = "Cacio e Pepe"
        mock_scraper.site_name.return_value = "Example Site"
        mock_scraper.author.return_value = "Test Chef"
        mock_scraper.total_time.return_value = 30
        mock_scraper.cook_time.return_value = 15
        mock_scraper.prep_time.return_value = 15
        mock_scraper.yields.return_value = "4 servings"
        mock_scraper.category.return_value = "Pasta"
        mock_scraper.cuisine.return_value = "Italian"
        mock_scraper.image.return_value = "https://example.com/img.jpg"
        mock_scraper.ingredients.return_value = ["pasta", "pecorino", "pepper"]
        mock_scraper.instructions_list.return_value = ["Boil pasta", "Add cheese"]
        mock_scraper.nutrients.return_value = {"calories": "400"}
        mock_scrape_me.return_value = mock_scraper

        result = scrape_recipe("https://example.com/recipe", dish="cacio_e_pepe")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, RecipeData)
        self.assertEqual(result.title, "Cacio e Pepe")
        self.assertEqual(result.dish, "cacio_e_pepe")
        self.assertEqual(result.ingredients, ["pasta", "pecorino", "pepper"])
        self.assertEqual(len(result.instructions), 2)

    @patch("examples.roman_pasta_recipes.scrape_me")
    def test_scrape_recipe_failure_returns_none(self, mock_scrape_me):
        """scrape_recipe should return None when scraping fails."""
        mock_scrape_me.side_effect = Exception("Network error")
        result = scrape_recipe("https://example.com/bad")
        self.assertIsNone(result)

    @patch("examples.roman_pasta_recipes.scrape_recipe")
    def test_scrape_roman_recipes_filters_by_dish(self, mock_scrape):
        """scrape_roman_recipes should only scrape the requested dishes."""
        mock_scrape.return_value = RecipeData(
            title="Test",
            url="https://example.com",
            dish="carbonara",
            source="Example",
            ingredients=["pasta"],
            instructions=["Cook"],
        )

        scrape_roman_recipes(dishes=["carbonara"])

        scraped_urls = [call.args[0] for call in mock_scrape.call_args_list]
        carbonara_urls = ROMAN_PASTA_RECIPES["carbonara"]
        self.assertEqual(scraped_urls, carbonara_urls)

    @patch("examples.roman_pasta_recipes.scrape_recipe")
    def test_scrape_roman_recipes_unknown_dish(self, mock_scrape):
        """scrape_roman_recipes should skip unknown dish names."""
        result = scrape_roman_recipes(dishes=["unknown_dish"])
        self.assertEqual(result, [])
        mock_scrape.assert_not_called()

    @patch("examples.roman_pasta_recipes.scrape_recipe")
    def test_scrape_roman_recipes_save_json(self, mock_scrape):
        """scrape_roman_recipes should save to JSON when output is given."""
        mock_scrape.return_value = RecipeData(
            title="Gricia",
            url="https://example.com/gricia",
            dish="gricia",
            source="Example",
            ingredients=["guanciale"],
            instructions=["Fry"],
        )
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            path = f.name
        try:
            scrape_roman_recipes(dishes=["gricia"], output=path)
            loaded = load_from_json(path)
            self.assertGreater(len(loaded), 0)
            self.assertEqual(loaded[0].title, "Gricia")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
