"""A code block in a PDF: MinerU writes it with its own fence (```txt ... ```), TextFold's reader without one; either
way the document has it as one block of code, and the paragraph after it as a paragraph.

Run from the repo root:
    python3 -m unittest discover tests
"""
import re
import unittest

from textfold import markdown, pdfdoc

AFTER = "The match statement above picks a branch by the shape of its value."


def doc(code, producer="mineru"):
    return {"metadata": {"file_suffix": "pdf", "producer": {"name": producer}}, "pages": [{"page_idx": 0, "blocks": [
        {"type": "paragraph_title", "content": "Pattern matching", "level": 2, "bbox": [0.1, 0.1, 0.9, 0.15]},
        {"type": "code", "sub_type": "code", "content": code, "bbox": [0.1, 0.2, 0.9, 0.4], "captions": [], "footnotes": []},
        {"type": "text", "content": AFTER, "bbox": [0.1, 0.45, 0.9, 0.5]},
    ]}]}


def html_of(code, producer="mineru"):
    _, _, md = pdfdoc.to_markdown(doc(code, producer), "x.pdf")
    return markdown.to_html(md)[0]


def code_blocks(html):
    return re.findall(r"<pre[^>]*>(.*?)</pre>", html, re.S)


class CodeFences(unittest.TestCase):
    def assertOneCodeThenProse(self, html, *lines):
        got = code_blocks(html)
        self.assertEqual(len(got), 1, html)
        for line in lines:
            self.assertIn(line, got[0])
        self.assertIn(f"<p>{AFTER}</p>", html)
        self.assertNotIn("```", html.replace(got[0], ""))

    def test_the_engines_own_fence_is_not_fenced_again(self):
        html = html_of("```txt\nx = 1\n```")
        self.assertOneCodeThenProse(html, "x = 1")
        self.assertNotIn("```", html)
        self.assertIn('class="language-txt"', html)   # its language kept

    def test_the_engines_fence_with_tildes_or_nothing_in_it(self):
        self.assertOneCodeThenProse(html_of("~~~c\nx = 1\n  ~~~"), "x = 1")
        html = html_of("```txt\n```")
        self.assertEqual(len(code_blocks(html)), 1, html)
        self.assertNotIn("```", html)

    def test_bare_code_is_fenced_once(self):
        html = html_of("x = 1", "pdf-inspector")
        self.assertOneCodeThenProse(html, "x = 1")
        self.assertNotIn("```", html)

    def test_a_snippet_of_markdown_read_by_textfold_keeps_its_fence(self):
        html = html_of("```python\nprint(1)\n```", "pdf-inspector")
        self.assertOneCodeThenProse(html, "```python", "print(1)")

    def test_code_with_a_fence_line_in_it(self):
        html = html_of("x = 1\n```\ny = 2")
        self.assertOneCodeThenProse(html, "x = 1", "```", "y = 2")

    def test_the_side_by_side_view_reads_the_code_without_its_fence(self):
        code = next(x for x in pdfdoc.layout_of(doc("```c\n#include <stdio.h>\n```")) if "stdio" in x["t"])
        self.assertEqual(code["t"], "#include <stdio.h>")

    def test_a_files_code_keeps_its_links_as_written(self):
        sc = doc("see [the spec](spec.md)", "textfold")
        sc["metadata"]["file_suffix"] = "docx"
        _, _, md = pdfdoc.to_markdown(sc, "x.docx")
        self.assertIn("```\nsee [the spec](spec.md)\n```", md)


if __name__ == "__main__":
    unittest.main()
