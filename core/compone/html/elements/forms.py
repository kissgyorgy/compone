from ..html_elements import _HTMLElement, _HTMLElementBase, _VoidHTMLElement

Datalist = _HTMLElement("datalist")
Fieldset = _HTMLElement("fieldset")
Button = _HTMLElement("button")
Form = _HTMLElement("form")
Input = _VoidHTMLElement("input")
Label = _HTMLElement("label")
Legend = _HTMLElement("legend")
Meter = _HTMLElement("meter")
Optgroup = _HTMLElement("optgroup")
Option = _HTMLElement("option")
Output = _HTMLElement("output")
Progress = _HTMLElement("progress")
Select = _HTMLElement("select")
Textarea = _HTMLElement("textarea")


class ButtonButton(_HTMLElementBase):
    _tag = "button"
    _attributes = {"type": "button"}


class ResetButton(_HTMLElementBase):
    _tag = "button"
    _attributes = {"type": "reset"}


class SubmitButton(_HTMLElementBase):
    _tag = "button"
    _attributes = {"type": "submit"}
