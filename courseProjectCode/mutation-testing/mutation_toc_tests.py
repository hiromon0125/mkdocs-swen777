"""Mutation-testing tests for ``mkdocs/structure/toc.py``

The existing suite never checks the ``active`` flag that ``get_toc()`` sets on
the first table-of-contents entry, and never passes more than one top-level
heading, so mutants that change the active flag or which entry receives it
survived.
"""

import unittest

from mkdocs.structure.toc import get_toc


def _token(name, id, level=1, children=None):
    return {'name': name, 'id': id, 'level': level, 'children': children or []}


class TocActiveFlagTests(unittest.TestCase):
    def test_first_top_level_item_is_marked_active(self):
        """Only the first top-level entry is marked active, and the flag is exactly ``True``."""
        toc = get_toc([_token('One', 'one'), _token('Two', 'two')])

        first, second = list(toc)
        self.assertIs(first.active, True)
        # Only the first entry is marked; later entries never get the attribute.
        self.assertFalse(hasattr(second, 'active'))

    def test_children_of_first_item_are_not_marked_active(self):
        """The active flag applies to the top-level entry only, not its children."""
        toc = get_toc([_token('Parent', 'parent', children=[_token('Child', 'child', level=2)])])

        parent = toc.items[0]
        self.assertIs(parent.active, True)
        self.assertFalse(hasattr(parent.children[0], 'active'))

    def test_empty_token_list_gives_empty_toc(self):
        """An empty token list must not raise and must produce an empty TOC."""
        toc = get_toc([])

        self.assertEqual(len(toc), 0)
        self.assertEqual(str(toc), '')


if __name__ == '__main__':
    unittest.main()
