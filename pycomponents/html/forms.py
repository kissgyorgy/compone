from ..component import _Elem, _HTMLComponent, _SelfElem

Datalist = _Elem("datalist")
Fieldset = _Elem("fieldset")
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


class Button(_HTMLComponent):
    name = "button"
    attributes = {"type": "button"}


class ResetButton(_HTMLComponent):
    name = "button"
    attributes = {"type": "reset"}


class SubmitButton(_HTMLComponent):
    name = "button"
    attributes = {"type": "submit"}
