from ..component import _Elem
from .content_sectioning import (
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    Address,
    Article,
    Aside,
    Footer,
    Header,
    Main,
    Nav,
    Section,
)
from .embedded import Embed, Iframe, Object, Picture, Portal, Source
from .forms import (
    Button,
    Datalist,
    Fieldset,
    Form,
    Input,
    Label,
    Legend,
    Meter,
    Optgroup,
    Option,
    Output,
    Progress,
    ResetButton,
    Select,
    SubmitButton,
    Textarea,
)
from .inline_text import (
    A,
    Abbr,
    B,
    Bdi,
    Bdo,
    Br,
    Cite,
    Code,
    Data,
    Del,
    Dfn,
    Em,
    I,
    Ins,
    Kbd,
    Mark,
    Q,
    Rp,
    Rt,
    Ruby,
    S,
    Samp,
    Small,
    Span,
    Strong,
    Sub,
    Sup,
    Time,
    U,
    Var,
    Wbr,
)
from .interactive import Details, Dialog, Summary
from .metadata import Base, Head, Link, Meta, Style, Title
from .multimedia import Area, Audio, Img, Map, Track, Video
from .scripting import Canvas, Noscript, Script
from .table import Caption, Col, Colgroup, Table, Tbody, Td, Tfoot, Th, Thead, Tr
from .text_content import (
    Blockquote,
    Dd,
    Div,
    Dl,
    Dt,
    Figcaption,
    Figure,
    Hr,
    Li,
    Menu,
    Ol,
    P,
    Pre,
    Ul,
)
from .web_components import Slot, Template

Html = _Elem("html")
Body = _Elem("body")

Svg = _Elem("svg")
Math = _Elem("math")
