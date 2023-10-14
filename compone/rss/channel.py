from ..component import _Elem, safe

Rss20 = safe('<rss version="2.0">')

# https://www.rssboard.org/rss-specification
Channel = _Elem("channel")

# Required sub-elements of channel
# FIXME: validate that these are present inside channel
Title = _Elem("title")
Link = _Elem("link")
Description = _Elem("description")

# Optional sub-elements of channel
# TODO: doscstrings for interpreter help and documentation
# FIXME: validate element content: https://www.rssboard.org/rss-language-codes
Language = _Elem("language")
Copyright = _Elem("copyright")
ManagingEditor = _Elem("managingEditor")
WebMaster = _Elem("webMaster")
PubDate = _Elem("pubDate")
LastBuildDate = _Elem("lastBuildDate")
Category = _Elem("category")
Generator = _Elem("generator")
Docs = _Elem("docs")
Cloud = _Elem("cloud")
# FIXME: validate that children is a number
Ttl = _Elem("ttl")
Rating = _Elem("rating")
TextInput = _Elem("textInput")
SkipHours = _Elem("skipHours")
SkipDays = _Elem("skipDays")
# FIXME: validate children
Day = _Elem("day")
