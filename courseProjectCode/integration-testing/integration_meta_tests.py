"""Integration tests for page titles set at the top of a Markdown page.

A page can start with a block of settings between two ``---`` lines (written
in YAML). MkDocs reads the block as settings instead of page text. Here it
sets the page's title:

    ---
    title: Custom Title
    ---

These tests build a small site and check that the title in that block flows
through these modules into the final HTML:

    mkdocs.config (load mkdocs.yml)
      -> mkdocs.commands.build (build the site)
      -> mkdocs.structure.files / mkdocs.structure.pages (find and read each page)
      -> mkdocs.utils.meta (split the settings block from the rest of the page)
      -> mkdocs.structure.nav (build the navigation from page titles)
      -> mkdocs.theme (render the browser-tab <title> and the nav bar)

Nothing is mocked.
"""

import logging
import os
import re
import tempfile
import unittest

from mkdocs.commands import build
from mkdocs.config import load_config


def build_site(root, pages):

    """Create a small MkDocs project in ``root`` with the given pages, build it,
and return the path to the built site folder.

``pages`` lists the files to create and what goes in each one. For example,
{'index.md': '# Home'} makes a file called index.md that contains "# Home".
"""

    docs = os.path.join(root, 'docs')
    os.makedirs(docs)

    for name, text in pages.items():
        with open(os.path.join(docs, name), 'w', encoding='utf-8') as f:
            f.write(text)

    config_file = os.path.join(root, 'mkdocs.yml')
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('site_name: Meta Test Site\n')

    # Builds the site    
    build.build(load_config(config_file=config_file))
    return os.path.join(root, 'site')


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def html_title(html):
    """Return the page's browser-tab title (the HTML <title>)."""
    return re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip()


def nav_labels(html):
    """Return the page titles in the top navigation bar (not the sidebar)."""
    # Cuts the pages HTML down to just the top part which contains the nav bar
    top_nav = html[: html.index('id="toc-collapse"')]
    return re.findall(r'class="nav-link[^"]*"[^>]*>(.*?)<', top_nav)


def sidebar_entries(html):
    """Return the entries in the page's table-of-contents sidebar."""
    # Cuts the pages HTML down to jusst the TOC sidebar
    sidebar = html[html.index('id="toc-collapse"') : html.index('role="main"')]
    return re.findall(r'href="#[^"]*"[^>]*>(.*?)<', sidebar)


class PageTitleBuildTests(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name

    def test_title_block_sets_page_title_in_nav_and_tab(self):

        """Normal case: the title in the settings block replaces the page's heading as its title."""
        
        site = build_site(
            self.root,
            {
                'index.md': '# Home\n',
                'guide.md': '---\ntitle: Custom Title\n---\n\n# Heading In Body\n\nGuide text.\n',
            },
        )

        html = read(os.path.join(site, 'guide', 'index.html'))

        self.assertEqual(html_title(html), 'Custom Title - Meta Test Site')

        self.assertIn('Custom Title', nav_labels(html))
        
        self.assertNotIn('title: Custom Title', html)

        self.assertIn('Guide text.', html)

    def test_invalid_title_block_is_shown_as_content_without_warning(self):
        """Edge case: a settings block that isn't valid YAML. Reproduces BUG-1 in report.md.

        The broken block is silently treated as page text. No warning is logged,
        the ``---`` lines show up as a horizontal line and a heading, and because
        the page no longer starts with its ``# Fallback Heading``, the title
        falls back to the filename ("Guide"). The broken line also shows up in
        the page's table of contents.
        """

        # "[unclosed" is missing its closing "]", so the settings block isn't valid YAML.
        with self.assertLogs('mkdocs', level='DEBUG') as logs:
            site = build_site(
                self.root,
                {
                    'index.md': '# Home\n',
                    'guide.md': '---\ntitle: [unclosed\n---\n\n# Fallback Heading\n\nGuide text.\n',
                },
            )

        html = read(os.path.join(site, 'guide', 'index.html'))

        # No warning or error is logged about the broken block.
        problems = [r for r in logs.records if r.levelno >= logging.WARNING]
        self.assertEqual(problems, [])

        # The broken block is shown on the page and listed in the table of contents.
        self.assertIn('<h2 id="title-unclosed">title: [unclosed</h2>', html)
        self.assertIn('title: [unclosed', sidebar_entries(html))

        # The page's own heading is not used as its title; the filename is.
        self.assertEqual(html_title(html), 'Guide - Meta Test Site')
        self.assertIn('Guide', nav_labels(html))
        self.assertNotIn('Fallback Heading', nav_labels(html))


if __name__ == '__main__':
    unittest.main()
