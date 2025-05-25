import pytest
from compone_bootstrap5.button import (
    ButtonDanger,
    ButtonDark,
    ButtonInfo,
    ButtonLight,
    ButtonLink,
    ButtonPrimary,
    ButtonSecondary,
    ButtonSuccess,
    ButtonWarning,
    CloseButton,
    Size,
)


@pytest.mark.parametrize(
    "button_component, expected_class",
    [
        (ButtonPrimary, "btn-primary"),
        (ButtonSecondary, "btn-secondary"),
        (ButtonSuccess, "btn-success"),
        (ButtonDanger, "btn-danger"),
        (ButtonWarning, "btn-warning"),
        (ButtonInfo, "btn-info"),
        (ButtonLight, "btn-light"),
        (ButtonDark, "btn-dark"),
        (ButtonLink, "btn-link"),
    ],
)
def test_button_variants(Button, expected_class):
    assert (
        str(Button["Click me"])
        == f'<button class="btn {expected_class}">Click me</button>'
    )


@pytest.mark.parametrize(
    "button_component, expected_variant",
    [
        (ButtonPrimary, "btn-outline-primary"),
        (ButtonSecondary, "btn-outline-secondary"),
        (ButtonSuccess, "btn-outline-success"),
        (ButtonDanger, "btn-outline-danger"),
        (ButtonWarning, "btn-outline-warning"),
        (ButtonInfo, "btn-outline-info"),
        (ButtonLight, "btn-outline-light"),
        (ButtonDark, "btn-outline-dark"),
    ],
)
def test_outline_button_variants(Button, expected_variant):
    assert (
        str(Button(outline=True)["Click me"])
        == f'<button class="btn {expected_variant}">Click me</button>'
    )


@pytest.mark.parametrize(
    "size, expected_size_class",
    [
        ("sm", "btn-sm"),
        ("lg", "btn-lg"),
        (Size.SMALL, "btn-sm"),
        (Size.LARGE, "btn-lg"),
    ],
)
def test_button_sizes(size, expected_size_class):
    assert (
        str(ButtonPrimary(size=size)["Click me"])
        == f'<button class="btn btn-primary {expected_size_class}">Click me</button>'
    )


def test_disabled_button():
    assert (
        str(ButtonDanger(disabled=True)["Disabled"])
        == '<button disabled class="btn btn-danger">Disabled</button>'
    )


def test_button_with_custom_attributes():
    assert str(
        ButtonSuccess(id="submit-btn", data_testid="submit-button", type="submit")[
            "Submit"
        ]
    ) == (
        '<button class="btn btn-success" id="submit-btn" data-testid="submit-button" type="submit">'  # noqa
        "Submit"
        "</button>"
    )


def test_button_outline_with_size_and_disabled():
    assert str(
        ButtonWarning(outline=True, size="lg", disabled=True)["Large Disabled Outline"]
    ) == (
        '<button disabled class="btn btn-outline-warning btn-lg">'
        "Large Disabled Outline"
        "</button>"
    )


def test_button_empty_content():
    assert str(ButtonInfo()) == '<button class="btn btn-info"></button>'


def test_button_link_no_outline():
    assert (
        str(ButtonLink(size="sm")["Link Button"])
        == '<button class="btn btn-link btn-sm">Link Button</button>'
    )


def test_close_button_default():
    assert str(CloseButton()) == (
        '<button class="btn-close" aria-label="Close" type="button"></button>'
    )


def test_close_button_dark():
    assert str(CloseButton(dark=True)) == (
        '<button class="btn-close" aria-label="Close" data-bs-theme="dark" type="button">'  # noqa
        "</button>"
    )


def test_close_button_disabled():
    assert str(CloseButton(disabled=True)) == (
        '<button disabled class="btn-close" aria-label="Close" type="button"></button>'
    )


def test_close_button_with_custom_attributes():
    assert str(CloseButton(data_bs_dismiss="modal", id="close-modal")) == (
        '<button class="btn-close" aria-label="Close" data-bs-dismiss="modal" id="close-modal" type="button">'  # noqa
        "</button>"
    )
