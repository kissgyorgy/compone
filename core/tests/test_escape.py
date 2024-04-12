from compone import escape, safe


def test_object_with_str():
    class SomeObject:
        def __str__(self):
            return "<script>Something harmful</script>"

    escaped = escape(SomeObject())
    assert escaped == "&lt;script&gt;Something harmful&lt;/script&gt;"


def test_object_with_safe_str():
    script = "<script>Something harmful</script>"

    class SomeObject:
        def __str__(self):
            return safe(script)

    escaped = escape(SomeObject())
    assert escaped == script


def test_appending_safe_escapes_appended():
    script = safe("<script>Good script</script>")
    harmful = "<script>Harmful user input</script>"
    expected = safe(
        "<script>Good script</script>&lt;script&gt;Harmful user input&lt;/script&gt;"
    )
    assert script + harmful == expected


def test_appending_safe_str_escapes_other():
    class SomeObject:
        def __str__(self):
            return safe("<script>Good script</script>")

    class AnotherObject:
        def __str__(self):
            return "<script>Harmful user input</script>"

    assert str(SomeObject()) + str(AnotherObject()) == safe(
        "<script>Good script</script>&lt;script&gt;Harmful user input&lt;/script&gt;"
    )


def test_escape_None():
    assert isinstance(escape(None), safe)
    assert isinstance(escape(None), str)
    assert escape(None) == safe("")
    assert escape(None) == ""
    assert str(escape(None)) == ""
