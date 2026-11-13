"""Integration tests for a page's table of contents in a real site build.

The theme shows a sidebar "table of contents" with a link to each heading on
the page. These tests build a small site and check that headings flow through
these modules into working sidebar links:

    mkdocs.config (load mkdocs.yml, including the default ``toc`` Markdown extension)
      -> mkdocs.commands.build (build the site)
      -> mkdocs.structure.pages (render the page's Markdown)
      -> markdown's toc extension (give each heading an id)
      -> mkdocs.structure.toc (turn those headings into the page's table of contents)
      -> mkdocs.theme (render the sidebar links)


"""

import os
import re
import tempfile
import unittest

from mkdocs.commands import build
from mkdocs.config import load_config


def build_page(root, markdown):

    """Build a project whose second page is ``markdown`` and return that page's HTML."""
    docs = os.path.join(root, 'docs')
    os.makedirs(docs)

    with open(os.path.join(docs, 'index.md'), 'w', encoding='utf-8') as f:
        f.write('# Home\n')

    with open(os.path.join(docs, 'page.md'), 'w', encoding='utf-8') as f:
        f.write(markdown)

    config_file = os.path.join(root, 'mkdocs.yml')

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('site_name: TOC Test Site\n')

    build.build(load_config(config_file=config_file))
    with open(os.path.join(root, 'site', 'page', 'index.html'), encoding='utf-8') as f:
        return f.read()


def sidebar_links(html):
    """Return the links in the page's sidebar, e.g. ['#install', '#setup'].

    Each link jumps to a heading on the same page; '#setup' goes to the heading with id="setup".
    """
    sidebar = html[html.index('id="toc-collapse"') : html.index('role="main"')]
    return re.findall(r'href="(#[^"]+)"', sidebar)


def heading_ids(html):
    main = html[html.index('role="main"') :]
    return re.findall(r'<h[1-6] id="([^"]+)"', main)


class TableOfContentsBuildTests(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name

    def test_sidebar_links_match_heading_ids(self):
        """Normal case: every sidebar link points to a heading, including duplicate headings."""

        html = build_page(
            self.root,
            '# Page\n\n## Install\n\nText.\n\n## Setup\n\nText.\n\n## Setup\n\nMore text.\n',
        )

        self.assertEqual(heading_ids(html), ['page', 'install', 'setup', 'setup_1'])
        
        self.assertEqual(sidebar_links(html), ['#page', '#install', '#setup', '#setup_1'])

    def test_page_without_headings_has_empty_table_of_contents(self):
        """Edge case: a page with no headings builds and has no sidebar links."""

        html = build_page(self.root, 'Some text with no headings.\n')

        self.assertEqual(heading_ids(html), [])
        self.assertEqual(sidebar_links(html), [])
        self.assertIn('Some text with no headings.', html)


if __name__ == '__main__':
    unittest.main()
