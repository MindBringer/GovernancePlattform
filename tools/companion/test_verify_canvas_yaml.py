import unittest

import yaml

from verify_canvas_yaml import validate_text


class CanvasYamlRegression(unittest.TestCase):
    def test_studio_30441_colon_failure(self):
        with self.assertRaises(yaml.YAMLError):
            validate_text('Screens:\n  scrShell:\n    Properties:\n      Text: ="Öffnen: " & Coalesce(ThisItem.Title, "Ohne Titel")\n')

    def test_block_keeps_formula_text(self):
        source = 'Screens:\n  scrShell:\n    Properties:\n      Text: |-\n        ="Öffnen: " & Coalesce(ThisItem.Title, "Ohne Titel")\n'
        validate_text(source)
        actual = yaml.load(source, Loader=yaml.BaseLoader)["Screens"]["scrShell"]["Properties"]["Text"]
        self.assertEqual(actual, '="Öffnen: " & Coalesce(ThisItem.Title, "Ohne Titel")')

    def test_valid_yaml_with_mapping_property_fails(self):
        with self.assertRaisesRegex(ValueError, "scalar formula"):
            validate_text('Screens:\n  scrShell:\n    Properties:\n      Text: {unexpected: mapping}\n')

    def test_duplicate_property_fails(self):
        with self.assertRaisesRegex(ValueError, "Duplicate Canvas key"):
            validate_text('Screens:\n  scrShell:\n    Properties:\n      Text: ="first"\n      Text: ="second"\n')


if __name__ == "__main__":
    unittest.main()
