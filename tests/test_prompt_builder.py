import unittest

from magic_image_fetcher import build_prompt


class PromptBuilderTests(unittest.TestCase):
    def test_build_prompt_inserts_extra_prompt_at_front_and_keeps_required_sections(self):
        note_fields = {
            "英文": "Apple",
            "中文": "蘋果",
            "領域": "水果",
            "例句": "An apple a day keeps the doctor away.",
            "字根": "ap-",
            "補充": "A common fruit.",
        }

        prompt = build_prompt(note_fields, extra_prompt="Pixar style, colorful lighting.")

        self.assertTrue(prompt.startswith("Pixar style, colorful lighting."))
        self.assertIn("Word:\nApple", prompt)
        self.assertIn("Chinese Meaning:\n蘋果", prompt)
        self.assertIn("Domain:\n水果", prompt)
        self.assertIn("Example Sentence:\nAn apple a day keeps the doctor away.", prompt)
        self.assertIn("Word Root:\nap-", prompt)
        self.assertIn("Additional Notes:\nA common fruit.", prompt)

    def test_build_prompt_omits_empty_optional_sections(self):
        note_fields = {
            "英文": "Banana",
            "中文": "香蕉",
            "領域": "水果",
            "例句": "Bananas are yellow.",
            "字根": "",
            "補充": "",
        }

        prompt = build_prompt(note_fields, extra_prompt="")

        self.assertNotIn("Word Root:", prompt)
        self.assertNotIn("Additional Notes:", prompt)
        self.assertIn("Word:\nBanana", prompt)
