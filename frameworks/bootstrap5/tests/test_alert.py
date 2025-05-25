import pytest
from compone_bootstrap5 import (
    AlertDanger,
    AlertDark,
    AlertInfo,
    AlertLight,
    AlertPrimary,
    AlertSecondary,
    AlertSuccess,
    AlertWarning,
)


@pytest.mark.parametrize(
    "alert_component, expected_class",
    [
        (AlertPrimary, "alert-primary"),
        (AlertSecondary, "alert-secondary"),
        (AlertSuccess, "alert-success"),
        (AlertDanger, "alert-danger"),
        (AlertWarning, "alert-warning"),
        (AlertInfo, "alert-info"),
        (AlertLight, "alert-light"),
        (AlertDark, "alert-dark"),
    ],
)
def test_alert_variants(alert_component, expected_class):
    alert = alert_component["Test message"]
    html_str = str(alert)
    expected_html = (
        f'<div class="alert {expected_class}" role="alert">Test message</div>'
    )
    assert html_str == expected_html


@pytest.mark.parametrize(
    "alert_component, expected_variant",
    [
        (AlertSuccess, "alert-success"),
        (AlertDanger, "alert-danger"),
        (AlertWarning, "alert-warning"),
        (AlertInfo, "alert-info"),
    ],
)
def test_specific_alert_components(alert_component, expected_variant):
    alert = alert_component(dismissible=True)["Component test"]
    html_str = str(alert)
    expected_html = (
        f'<div class="alert {expected_variant} alert-dismissible fade show" role="alert">'  # noqa
        "Component test"
        '<button class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'
        "</div>"
    )
    assert html_str == expected_html


def test_alert_custom_attributes():
    alert = AlertDanger(id="my-alert", data_testid="alert-component")["Custom alert"]
    html_str = str(alert)
    expected_html = (
        '<div class="alert alert-danger" role="alert" id="my-alert" data-testid="alert-component">'  # noqa
        "Custom alert"
        "</div>"
    )
    assert html_str == expected_html


def test_alert_empty_content():
    alert = AlertInfo()
    html_str = str(alert)
    expected_html = '<div class="alert alert-info" role="alert"></div>'
    assert html_str == expected_html
