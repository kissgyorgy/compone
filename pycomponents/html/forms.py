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
    html_tag = "button"
    attributes = {"type": "button"}


class ResetButton(_HTMLComponent):
    html_tag = "button"
    attributes = {"type": "reset"}


class SubmitButton(_HTMLComponent):
    html_tag = "button"
    attributes = {"type": "submit"}
