"""Mutation-testing tests for ``mkdocs/utils/meta.py``

``meta.py`` reads the metadata block (YAML or MultiMarkdown, e.g. ``Title: Top``)
at the top of a Markdown document. These tests cover its one function,
``get_data()``, and the import at the top of the file that picks PyYAML's fast
C loader (``CSafeLoader``) or falls back to the pure-Python ``SafeLoader``.

The existing tests never put a plain-text line straight after a metadata key,
never use a whitespace-only separator line, and never exercise the fallback
used when PyYAML's C loader is unavailable, so several mutants survived.
"""

import importlib
import sys
import types
import unittest
from unittest import mock

import yaml

from mkdocs.utils import meta


class MultiMarkdownParsingTests(unittest.TestCase):
    def test_non_metadata_line_after_key_stops_parsing(self):
        """The first non-metadata line ends the block and is put back in its original place.

        Kills the mutants that change ``m2 and key`` to ``or`` (crashes) and
        ``lines.insert(0, line)`` to ``insert(1, ...)`` or ``insert(-1, ...)``.
        Three body lines are needed so the insert position is visible.
        """
        doc = 'Title: Top\nplain text\nsecond line\nthird line'

        self.assertEqual(
            meta.get_data(doc), ('plain text\nsecond line\nthird line', {'title': 'Top'})
        )

    def test_whitespace_only_line_ends_metadata(self):
        """A line of spaces counts as the blank separator and is removed.

        Kills the mutant that changes ``line.strip() == ''`` to ``< ''``.
        """
        doc = 'Title: Top\n   \nBody'

        self.assertEqual(meta.get_data(doc), ('Body', {'title': 'Top'}))


class SafeLoaderFallbackTests(unittest.TestCase):
    def test_falls_back_to_pure_python_loader_without_libyaml(self):
        """meta.py still works when PyYAML's fast C loader isn't installed.

        meta.py tries ``from yaml import CSafeLoader`` (fast, needs libyaml) and falls
        back to the pure-Python ``yaml.SafeLoader`` if that import fails. This test
        swaps in a fake ``yaml`` module without ``CSafeLoader``, reloads meta.py, and
        checks it chose ``SafeLoader`` and can still parse YAML.

        Kills the mutant that removes the ``except ImportError`` fallback (meta.py
        would crash on import).
        """
        fake_yaml = types.ModuleType('yaml')
        # Copy everything from the real yaml module except CSafeLoader (like PyYAML without libyaml).
        fake_yaml.__dict__.update({k: v for k, v in vars(yaml).items() if k != 'CSafeLoader'})
        # Re-import the real module afterwards so other tests see the normal loader.
        self.addCleanup(importlib.reload, meta)

        with mock.patch.dict(sys.modules, {'yaml': fake_yaml}):
            importlib.reload(meta)

            self.assertIs(meta.SafeLoader, yaml.SafeLoader)
            self.assertEqual(meta.get_data('---\ntitle: T\n---\nBody'), ('Body', {'title': 'T'}))


if __name__ == '__main__':
    unittest.main()
