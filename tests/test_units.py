from editor_autopilot.checks import check_units


def test_variable_unit_conflict():
    paragraphs = ["指标A: 120 mmHg", "指标A: 16 cm"]
    issues = check_units(paragraphs, [], ["mmHg", "mg/L", "mmol/L", "kg", "cm", "min", "h", "%"])
    assert any("多个单位" in i.message for i in issues)
