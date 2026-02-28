import unittest
from unittest.mock import patch, MagicMock

from examples.roman_pasta_recipes import (
    ROMAN_PASTA_RECIPES,
    scrape_recipe,
    scrape_roman_recipes,
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

    def test_safe_call_returns_value(self):
        """_safe_call should return the function result on success."""
        self.assertEqual(_safe_call(lambda: 42), 42)

    def test_safe_call_returns_none_on_error(self):
        """_safe_call should return None when the function raises."""

        def failing():
            raise ValueError("boom")

        self.assertIsNone(_safe_call(failing))

    @patch("examples.roman_pasta_recipes.scrape_me")
    def test_scrape_recipe_success(self, mock_scrape_me):
        """scrape_recipe should return a dict with recipe data on success."""
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = "Cacio e Pepe"
        mock_scraper.author.return_value = "Test Chef"
        mock_scraper.total_time.return_value = 30
        mock_scraper.yields.return_value = "4 servings"
        mock_scraper.ingredients.return_value = ["pasta", "pecorino", "pepper"]
        mock_scraper.instructions_list.return_value = ["Boil pasta", "Add cheese"]
        mock_scrape_me.return_value = mock_scraper

        result = scrape_recipe("https://example.com/recipe")
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Cacio e Pepe")
        self.assertEqual(result["ingredients"], ["pasta", "pecorino", "pepper"])
        self.assertEqual(len(result["instructions"]), 2)

    @patch("examples.roman_pasta_recipes.scrape_me")
    def test_scrape_recipe_failure_returns_none(self, mock_scrape_me):
        """scrape_recipe should return None when scraping fails."""
        mock_scrape_me.side_effect = Exception("Network error")
        result = scrape_recipe("https://example.com/bad")
        self.assertIsNone(result)

    @patch("examples.roman_pasta_recipes.scrape_recipe")
    def test_scrape_roman_recipes_filters_by_dish(self, mock_scrape):
        """scrape_roman_recipes should only scrape the requested dishes."""
        mock_scrape.return_value = {
            "title": "Test",
            "url": "https://example.com",
            "author": "Chef",
            "total_time": 30,
            "yields": "4 servings",
            "ingredients": ["pasta"],
            "instructions": ["Cook"],
        }

        scrape_roman_recipes(dishes=["carbonara"], as_json=False)

        scraped_urls = [call.args[0] for call in mock_scrape.call_args_list]
        carbonara_urls = ROMAN_PASTA_RECIPES["carbonara"]
        self.assertEqual(scraped_urls, carbonara_urls)

    @patch("examples.roman_pasta_recipes.scrape_recipe")
    def test_scrape_roman_recipes_unknown_dish(self, mock_scrape):
        """scrape_roman_recipes should skip unknown dish names."""
        result = scrape_roman_recipes(dishes=["unknown_dish"], as_json=False)
        self.assertEqual(result, [])
        mock_scrape.assert_not_called()


if __name__ == "__main__":
    unittest.main()
