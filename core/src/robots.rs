use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyModule};

use crate::component::make_func_component;
use crate::escape::safe_empty;
use crate::python_package::{add_aliases, make_package, register_child};

pub fn add_module(py: Python<'_>, root: &Bound<'_, PyModule>) -> PyResult<()> {
    let robots = make_package(py, "compone.robots")?;

    let robots_txt = PyModule::new(py, "compone.robots.robots_txt")?;
    robots_txt.add("Bot", make_bot_enum(py)?)?;

    macro_rules! add_component {
        ($function:ident, $name:literal) => {{
            let function = wrap_pyfunction!($function, &robots_txt)?;
            robots_txt.add($name, make_func_component(&function)?)?;
        }};
    }

    add_component!(render_robots_txt, "RobotsTxt");
    add_component!(render_entry, "Entry");
    add_component!(render_user_agent, "UserAgent");
    add_component!(render_disallow, "Disallow");
    add_component!(render_allow, "Allow");
    add_component!(render_crawl_delay, "CrawDelay");
    add_component!(render_sitemap, "Sitemap");
    register_child(py, &robots, "robots_txt", &robots_txt)?;

    let html_meta = PyModule::new(py, "compone.robots.html_meta")?;
    let meta_tag_function = wrap_pyfunction!(render_meta_tag, &html_meta)?;
    html_meta.add("MetaTag", make_func_component(&meta_tag_function)?)?;
    register_child(py, &robots, "html_meta", &html_meta)?;

    add_aliases(
        &robots,
        &robots_txt,
        &[
            "Allow",
            "Bot",
            "CrawDelay",
            "Disallow",
            "Entry",
            "RobotsTxt",
            "Sitemap",
            "UserAgent",
        ],
    )?;
    add_aliases(&robots, &html_meta, &["MetaTag"])?;
    register_child(py, root, "robots", &robots)
}

fn make_bot_enum(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let members = PyDict::new(py);
    for (name, value) in [
        ("All", "*"),
        ("Google", "Googlebot"),
        ("Bing", "Bingbot"),
        ("Yahoo", "Slurp"),
        ("Yandex", "Yandex"),
        ("Baidu", "BaiduSpider"),
        ("DuckDuckGo", "DuckDuckBot"),
        ("Twitter", "Twitterbot"),
    ] {
        members.set_item(name, value)?;
    }
    let bot = py.import("enum")?.getattr("Enum")?.call1(("Bot", members))?;
    bot.setattr("__module__", "compone.robots.robots_txt")?;
    Ok(bot.unbind())
}

#[pyfunction(name = "RobotsTxt", signature = (*, children))]
fn render_robots_txt(children: Py<PyAny>) -> Py<PyAny> {
    children
}

#[pyfunction(
    name = "Entry",
    signature = (*, user_agent, disallow, allow=None, crawdelay=None, sitemap=None)
)]
fn render_entry(
    py: Python<'_>,
    user_agent: &Bound<'_, PyAny>,
    disallow: &Bound<'_, PyAny>,
    allow: Option<&Bound<'_, PyAny>>,
    crawdelay: Option<&Bound<'_, PyAny>>,
    sitemap: Option<&Bound<'_, PyAny>>,
) -> PyResult<Py<PyAny>> {
    let lines = PyList::empty(py);
    let agent = user_agent.getattr("value")?.str()?;
    lines.append(format!("User-agent: {agent}\n"))?;

    for path in disallow.try_iter()? {
        lines.append(format!("Disallow: {}\n", path?.str()?))?;
    }
    if let Some(allow) = allow {
        for path in allow.try_iter()? {
            lines.append(format!("Allow: {}\n", path?.str()?))?;
        }
    }
    if let Some(crawdelay) = crawdelay.filter(|value| value.is_truthy().unwrap_or(false)) {
        lines.append(format!("Crawl-delay: {}\n", crawdelay.str()?))?;
    }
    if let Some(sitemap) = sitemap.filter(|value| value.is_truthy().unwrap_or(false)) {
        lines.append(format!("Sitemap: {}\n", sitemap.str()?))?;
    }
    lines.append("\n")?;
    Ok(lines.unbind().into_any())
}

#[pyfunction(name = "UserAgent", signature = (*, agent))]
fn render_user_agent(agent: &Bound<'_, PyAny>) -> PyResult<String> {
    Ok(format!("User-agent: {}\n", agent.getattr("value")?.str()?))
}

#[pyfunction(name = "Disallow", signature = (*, path))]
fn render_disallow(path: &Bound<'_, PyAny>) -> PyResult<String> {
    Ok(format!("Disallow: {}\n", path.str()?))
}

#[pyfunction(name = "Allow", signature = (*, path))]
fn render_allow(path: &Bound<'_, PyAny>) -> PyResult<String> {
    Ok(format!("Allow: {}\n", path.str()?))
}

#[pyfunction(name = "CrawDelay", signature = (*, delay))]
fn render_crawl_delay(delay: &Bound<'_, PyAny>) -> PyResult<String> {
    Ok(format!("Crawl-delay: {}\n", delay.str()?))
}

#[pyfunction(name = "Sitemap", signature = (*, url))]
fn render_sitemap(url: &Bound<'_, PyAny>) -> PyResult<String> {
    Ok(format!("Sitemap: {}\n", url.str()?))
}

#[pyfunction(
    name = "MetaTag",
    signature = (*, index=false, follow=false, archive=true, snippet=true)
)]
fn render_meta_tag(
    py: Python<'_>,
    index: bool,
    follow: bool,
    archive: bool,
    snippet: bool,
) -> PyResult<Py<PyAny>> {
    let mut directives = Vec::with_capacity(4);
    if !index {
        directives.push("noindex");
    }
    if !follow {
        directives.push("nofollow");
    }
    if !archive {
        directives.push("noarchive");
    }
    if !snippet {
        directives.push("nosnippet");
    }

    if directives.is_empty() {
        return safe_empty(py);
    }

    let kwargs = PyDict::new(py);
    kwargs.set_item("name", "robots")?;
    kwargs.set_item("content", directives.join(", "))?;
    py.import("compone")?
        .getattr("html")?
        .getattr("Meta")?
        .call((), Some(&kwargs))
        .map(Bound::unbind)
}
