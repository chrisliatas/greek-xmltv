import contextlib
import io
import unittest

from lxml import etree as et

from xmltv.postproc import _split_rating_and_title
from xmltv.postproc import JsonToXmltv


def _render_programme(title: str):
    generator = object.__new__(JsonToXmltv)
    generator._dataloaded = True
    generator.json_data = [
        {
            "id": ["channel-01"],
            "name": ["ERT1"],
            "region": ["National-public"],
            "programmes": [
                {
                    "airDateTime": "20260801050000 +0300",
                    "title": title,
                    "desc": "description",
                }
            ],
        }
    ]
    generator.chnl_cache = {"channel-01": {"id": "1", "hashd": False}}
    generator.root = et.Element("tv")
    generator.xtree = et.ElementTree(generator.root)
    generator.tree_loaded = False
    generator.load_cache = lambda: None
    generator.write_xml_file = lambda: None
    with contextlib.redirect_stdout(io.StringIO()):
        generator.generate_xmltv(write_file=False)
    return generator.root.find("programme")


class ProgrammeTitleParsingTests(unittest.TestCase):
    def test_preserves_current_ert_titles_without_rating_prefix(self) -> None:
        self.assertEqual(
            _split_rating_and_title("Σαββατοκύριακο Ειδήσεις"),
            ("[K16]", "Σαββατοκύριακο Ειδήσεις"),
        )

    def test_extracts_legacy_bracketed_rating(self) -> None:
        self.assertEqual(
            _split_rating_and_title("[K16] Δελτίο Ειδήσεων"),
            ("[K16]", "Δελτίο Ειδήσεων"),
        )

    def test_preserves_one_word_titles(self) -> None:
        self.assertEqual(
            _split_rating_and_title("Ειδήσεις"),
            ("[K16]", "Ειδήσεις"),
        )

    def test_does_not_treat_bracketed_title_text_as_rating(self) -> None:
        self.assertEqual(
            _split_rating_and_title("[Αθλητικά] Νέα"),
            ("[K16]", "[Αθλητικά] Νέα"),
        )

    def test_generate_xmltv_preserves_ert_title_and_default_rating(self) -> None:
        programme = _render_programme("Σαββατοκύριακο Ειδήσεις")
        self.assertEqual(programme.findtext("title"), "Σαββατοκύριακο Ειδήσεις")
        self.assertEqual(programme.findtext("rating/value"), "K16")

    def test_generate_xmltv_extracts_legacy_rating(self) -> None:
        programme = _render_programme("[K8] Δελτίο Ειδήσεων")
        self.assertEqual(programme.findtext("title"), "Δελτίο Ειδήσεων")
        self.assertEqual(programme.findtext("rating/value"), "K8")
