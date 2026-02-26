from editor_autopilot.checks import check_numbering


def test_numbering_detects_gap():
    paragraphs = ["1 引言", "2 方法", "4 结果"]
    issues = check_numbering(paragraphs)
    assert any("不连续" in i.message for i in issues)
