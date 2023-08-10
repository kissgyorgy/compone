from ..component import Elem, SelfElem, _HTMLComponent

Datalist = Elem("datalist")
Fieldset = Elem("fieldset")
Form = Elem("form")
Input = SelfElem("input")
Label = Elem("label")
Legend = Elem("legend")
Meter = Elem("meter")
Optgroup = Elem("optgroup")
Option = Elem("option")
Output = Elem("output")
Progress = Elem("progress")
Select = Elem("select")
Textarea = Elem("textarea")


class Button(_HTMLComponent):
    name = "button"
    attributes = {"type": "button"}


class ResetButton(_HTMLComponent):
    name = "button"
    attributes = {"type": "reset"}


class SubmitButton(_HTMLComponent):
    name = "button"
    attributes = {"type": "submit"}
