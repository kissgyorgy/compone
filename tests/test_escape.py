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
