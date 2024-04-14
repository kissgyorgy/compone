from compone.utils import snake_to_camel_case


def test_snake_case():
    assert snake_to_camel_case("snake_case") == "snakeCase"
    assert snake_to_camel_case("Snake_case") == "SnakeCase"
    assert snake_to_camel_case("SnakeCase") == "SnakeCase"
