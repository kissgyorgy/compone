from ..component import _Elem, _HTMLComponent, _SelfElem

Datalist = _Elem("datalist")
Fieldset = _Elem("fieldset")
Button = _Elem("button")
Form = _Elem("form")
Input = _SelfElem("input")
Label = _Elem("label")
Legend = _Elem("legend")
Meter = _Elem("meter")
Optgroup = _Elem("optgroup")
Option = _Elem("option")
Output = _Elem("output")
Progress = _Elem("progress")
Select = _Elem("select")
Textarea = _Elem("textarea")


class ButtonButton(_HTMLComponent):
    _html_tag = "button"
    _attributes = {"type": "button"}


class ResetButton(_HTMLComponent):
    _html_tag = "button"
    _attributes = {"type": "reset"}


class SubmitButton(_HTMLComponent):
    _html_tag = "button"
    _attributes = {"type": "submit"}
