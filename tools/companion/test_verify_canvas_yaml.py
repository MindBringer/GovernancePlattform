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

    def test_native_pa2108_classic_button_accessible_label(self):
        with self.assertRaisesRegex(ValueError, "PA2108: Classic/Button"):
            validate_text('Screens:\n  scrShell:\n    Children:\n      - arbitraryDecision:\n          Control: Classic/Button@2.2.0\n          Properties:\n            Text: ="Genehmigen"\n            AccessibleLabel: ="Entscheidung"\n')

    def test_classic_button_text_and_tooltip(self):
        validate_text('Screens:\n  scrShell:\n    Children:\n      - arbitraryDecision:\n          Control: Classic/Button@2.2.0\n          Properties:\n            Text: ="Genehmigen"\n            Tooltip: ="Anschließend speichern"\n')

    def test_input_accessible_label_is_preserved(self):
        validate_text('Screens:\n  scrShell:\n    Children:\n      - input:\n          Control: Classic/TextInput@2.3.2\n          Properties:\n            AccessibleLabel: ="Titel"\n')


if __name__ == "__main__":
    unittest.main()
