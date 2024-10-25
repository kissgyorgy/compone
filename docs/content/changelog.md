## 0.4.0
This is the biggest release yet, very close to the final API, but
I want people to try it out first before I release 1.0.0.
I'm using compone in production for years now.

- Simplify APIs, remove `__call__`
- Disallow using Python keywords as arguments, now only the underscore versions
  are allowed (e.g. `class_` instead of `class`).
- `escape` now escapes iterables too by concatenating the escaped elements
- Allow function components with `@lru_cache`


## 0.3.0
All HTML elements are Components now instead of safe objects.
Even `html.Br` can have attributes.


## 0.2.1
Compatibility with non-str objects like Django `gettext_lazy`.


## 0.2.0
- HTMX helpers.
- `classes` HTML attribute helper.
- Preline UI Component Framework sketch.


## 0.1.0
After lots of experimentation for a nice API, this is the first version 
where I was satisfied with the API.

All the HTML elements were implemented in this version and I made it
work with Flask and Django.

Custom autoescaping was implemented in this version too, but later I
switched to MarkupSafe.

Tried to implement React-like "hooks", but it made no sense in Python world,
so I abandoned that idea.

Started compone Stories, which is already useful.

I already used this version in production for months, later versions only
refined the API and made convenience features.
