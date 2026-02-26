from editor_autopilot.checks import check_abstract_consistency


def test_abstract_sample_size_mismatch():
    paragraphs = [
        "摘要 目的：观察效果。方法：随机分组，n=120。结果：有效。结论：可行。",
        "方法 本研究纳入患者 n=118。",
        "结果 观察组优于对照组。",
    ]
    score, mismatches = check_abstract_consistency(paragraphs)
    assert score < 1
    assert any("n=120" in m for m in mismatches)
