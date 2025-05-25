import pytest
from compone_bootstrap5.badge import (
    BadgeDanger,
    BadgeDark,
    BadgeInfo,
    BadgeLight,
    BadgePrimary,
    BadgeSecondary,
    BadgeSuccess,
    BadgeWarning,
)


@pytest.mark.parametrize(
    "badge_component, expected_class",
    [
        (BadgePrimary, "text-bg-primary"),
        (BadgeSecondary, "text-bg-secondary"),
        (BadgeSuccess, "text-bg-success"),
        (BadgeDanger, "text-bg-danger"),
        (BadgeWarning, "text-bg-warning"),
        (BadgeInfo, "text-bg-info"),
        (BadgeLight, "text-bg-light"),
        (BadgeDark, "text-bg-dark"),
    ],
)
def test_badge_variants(badge_component, expected_class):
    badge = badge_component["New"]
    html_str = str(badge)
    expected_html = f'<span class="badge {expected_class}">New</span>'
    assert html_str == expected_html


@pytest.mark.parametrize(
    "badge_component, expected_variant",
    [
        (BadgeSuccess, "text-bg-success"),
        (BadgeDanger, "text-bg-danger"),
        (BadgeWarning, "text-bg-warning"),
        (BadgeInfo, "text-bg-info"),
    ],
)
def test_pill_badge_components(badge_component, expected_variant):
    badge = badge_component(pill=True)["99+"]
    html_str = str(badge)
    expected_html = f'<span class="badge {expected_variant} rounded-pill">99+</span>'
    assert html_str == expected_html


def test_badge_custom_attributes():
    badge = BadgeDanger(id="notification-count", data_testid="badge-component")["5"]
    html_str = str(badge)
    expected_html = (
        '<span class="badge text-bg-danger" id="notification-count" data-testid="badge-component">'  # noqa
        "5"
        "</span>"
    )
    assert html_str == expected_html


def test_badge_empty_content():
    badge = BadgeInfo()
    html_str = str(badge)
    expected_html = '<span class="badge text-bg-info"></span>'
    assert html_str == expected_html


def test_badge_pill_with_custom_attributes():
    badge = BadgePrimary(pill=True, title="Notification count")["42"]
    html_str = str(badge)
    expected_html = (
        '<span class="badge text-bg-primary rounded-pill" title="Notification count">'
        "42"
        "</span>"
    )
    assert html_str == expected_html
