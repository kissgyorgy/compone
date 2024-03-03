import pytest

from compone import xml


def test_versions():
    assert xml.Xml10 == '<?xml version="1.0" encoding="UTF-8"?>'
    with pytest.raises(TypeError):
        xml.Xml10["cannot have children"]

    assert xml.Xml11 == '<?xml version="1.1" encoding="UTF-8"?>'
    with pytest.raises(TypeError):
        xml.Xml11["cannot have children"]


def test_comments_are_unescaped():
    unsafe_comment = "<script> and # some comments // but can\n be anything"
    res = xml.Comment[unsafe_comment]
    assert res == f"<-- {unsafe_comment} -->"
