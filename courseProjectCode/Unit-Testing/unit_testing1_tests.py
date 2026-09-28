

import logging
import os
import tempfile
import unittest

from mkdocs import exceptions, utils
from mkdocs.commands import new
from mkdocs.theme import Theme
from mkdocs.utils import yaml as mkdocs_yaml


class YamlTests(unittest.TestCase):
    """mkdocs/utils/yaml.py tests"""

    def test_bad_yaml_raises_configuration_error(self):
        # Covers lines 133-134
        # This config is broken: the line is never closed with "]"
        broken_config = "site_name: [unclosed"

        try:
            mkdocs_yaml.yaml_load(broken_config)
            self.fail("Expected a ConfigurationError, but no error was raised")
        except exceptions.ConfigurationError:
            pass  # This is what we want, so the test passes

    def test_empty_yaml_returns_empty_dict(self):
        # Covers line 138
        # An empty config file should give back an empty dictionary, not None
        empty_config = ""

        result = mkdocs_yaml.yaml_load(empty_config)

        self.assertEqual(result, {})


class UtilsTests(unittest.TestCase):
    """mkdocs/utils/__init__.py tests"""

    def test_warning_filter_still_works(self):
        # Covers lines 403-406
        # warning_filter is an old feature that should still give back a logging filter
        old_filter = utils.warning_filter

        self.assertEqual(type(old_filter), logging.Filter)

    def test_unknown_attribute_raises_error(self):
        # Covers line 408
        # Asking utils for something that doesn't exist should raise an AttributeError
        try:
            utils.not_a_real_attribute
            self.fail("Expected an AttributeError, but no error was raised")
        except AttributeError:
            pass  # This is what we want, so the test passes

    def test_path_to_url_converts_backslashes(self):
        # Covers lines 250-253
        # Windows style backslashes should be turned into URL style forward slashes
        windows_path = "folder\\file.md"

        url = utils.path_to_url(windows_path)

        self.assertEqual(url, "folder/file.md")

    def test_markdown_title_none_when_first_line_is_not_heading(self):
        # Covers line 312
        # The first line is plain text, not a "# Heading", so there is no title
        markdown = "Just some text\n# Heading"

        result = utils.get_markdown_title(markdown)

        self.assertIsNone(result)

    def test_markdown_title_none_for_blank_input(self):
        # Covers line 316
        # A page with only blank lines has no title
        markdown = "\n\n   \n"

        result = utils.get_markdown_title(markdown)

        self.assertIsNone(result)

    def test_create_media_urls_joins_base(self):
        # Covers line 246
        # Each file path should get the base folder added to the front
        paths = ["css/style.css", "js/app.js"]

        result = utils.create_media_urls(paths, base="assets")

        self.assertEqual(result, ["assets/css/style.css", "assets/js/app.js"])

    def test_clean_directory_keeps_hidden_files(self):
        # Covers line 143
        # Cleaning a folder should delete normal files but keep hidden ones
        with tempfile.TemporaryDirectory() as folder:
            hidden_file = os.path.join(folder, ".hidden")
            normal_file = os.path.join(folder, "visible.txt")
            open(hidden_file, "w").close()
            open(normal_file, "w").close()

            utils.clean_directory(folder)

            self.assertTrue(os.path.exists(hidden_file))
            self.assertFalse(os.path.exists(normal_file))


class ThemeTests(unittest.TestCase):
    """mkdocs/theme.py tests"""

    def test_private_vars_still_returns_theme_settings(self):
        # Covers lines 87-91
        
        theme = Theme(name="mkdocs")

        theme_settings = theme._vars

        self.assertEqual(theme_settings["name"], "mkdocs")

    def test_delete_key_from_theme(self):
        # Covers lines 113 and 119
        # Deleting a theme setting should remove it and lower the count by one
        theme = Theme(name="mkdocs", my_key="hello")
        size_before = len(theme)

        removed_value = theme.pop("my_key")

        self.assertEqual(removed_value, "hello")
        self.assertFalse("my_key" in theme)
        self.assertEqual(len(theme), size_before - 1)


class NewProjectTests(unittest.TestCase):
    """mkdocs/commands/new.py tests"""

    def test_new_does_not_overwrite_existing_config(self):
        # Covers lines 35-36
        # Running "mkdocs new" on an existing project must not replace the user's mkdocs.yml
        with tempfile.TemporaryDirectory() as folder:
            config_path = os.path.join(folder, "mkdocs.yml")
            with open(config_path, "w") as f:
                f.write("site_name: Mine")

            new.new(folder)

            with open(config_path) as f:
                self.assertEqual(f.read(), "site_name: Mine")

    def test_new_does_not_overwrite_existing_index(self):
        # Covers line 47
        # Running "mkdocs new" must not replace a homepage (docs/index.md) that already exists
        with tempfile.TemporaryDirectory() as folder:
            os.mkdir(os.path.join(folder, "docs"))
            index_path = os.path.join(folder, "docs", "index.md")
            with open(index_path, "w") as f:
                f.write("# My page")

            new.new(folder)

            with open(index_path) as f:
                self.assertEqual(f.read(), "# My page")

    def test_new_in_existing_empty_folder(self):
        # Covers branch 38->42 (folder already exists, so it is not created)
        # "mkdocs new" should still create the config and homepage in an existing empty folder
        with tempfile.TemporaryDirectory() as folder:
            new.new(folder)

            self.assertTrue(os.path.exists(os.path.join(folder, "mkdocs.yml")))
            self.assertTrue(os.path.exists(os.path.join(folder, "docs", "index.md")))


class ExceptionTests(unittest.TestCase):
    """mkdocs/exceptions.py tests"""

    def test_abort_exits_with_code_1(self):
        # Abort is what MkDocs raises to stop a build, so it must exit with an error code
        try:
            raise exceptions.Abort("Build stopped")
        except SystemExit as error:
            self.assertEqual(error.code, 1)  # Exit code 1 means "failed"


if __name__ == "__main__":
    unittest.main()