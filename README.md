# Kaze (風)

A small static site generator in one Python file.

Kaze builds agency and small-business sites (home, about, contact, articles, case studies) from JSON and Markdown. It uses only the Python standard library, so a fresh Python 3.8+ install can build it with nothing to install.

Live site, built with Kaze: https://kaze.subimpact.net

## Is Kaze right for you?

Kaze is deliberately small. Use it when:

- your site fits the built-in page types, and
- you want a build step you can read and change yourself (`build.py` is under 500 lines).

Use something else when you need more:

- **[Hugo](https://gohugo.io/)**: mature, very fast, many themes, single binary.
- **[Pelican](https://getpelican.com/)**: full-featured Python generator with Jinja2 and plugins.
- **[Eleventy](https://www.11ty.dev/)**: flexible templating for Node.js users.
- **[Astro](https://astro.build/)**: components, client-side interactivity, integrations.

## Limitations

- **Fixed page types.** Adding a new kind of page means editing `build.py`.
- **Basic Markdown.** Supported: `#` to `####` headings, paragraphs, bold, italic, inline code, links, fenced code blocks, one-level lists, blockquotes, `---` rules. Not supported: tables, images, nested lists. Raw HTML in Markdown is escaped.
- **Minimal templates.** `{{placeholder}}` replacement plus `<!-- if:flag --> ... <!-- endif:flag -->` blocks. No loops or inheritance; repeated cards are rendered in Python.
- **No plugins, themes, or image processing.**

## Quickstart

```bash
git clone https://github.com/subimpact/kaze.git my-site
cd my-site
python3 dev.py      # preview at http://localhost:8000, rebuilds on change (refresh to see it)
python3 build.py    # write the site to dist/
```

The build deletes and recreates `dist/` every time, prints `[WARN]` lines for unfilled placeholders or missing files, and stops with an error on malformed JSON.

## Project layout

```text
content/
  site.json          name, URL, description, nav, homepage stats and features, page titles
  team.json          people shown on the about page
  articles/*.json    articles (Markdown body inside the JSON)
  case-studies/*.json  optional; the section is hidden when empty
templates/           plain HTML templates
static/              copied as-is into dist/ (CSS, JS, images)
admin/               optional Sveltia CMS config (see below)
build.py             the generator
dev.py               local preview server
```

## Output

- One HTML page per route, plus `sitemap.xml`.
- Article JSON-LD on every article, and FAQPage JSON-LD when an article has a `faq` list.
- Open Graph and Twitter tags. Set `og_image` in `site.json` to a file under `static/` to include an image.

## Editing content

Edit the JSON files in any editor. Article bodies are Markdown strings inside the JSON.

`admin/` contains an optional [Sveltia CMS](https://github.com/sveltia/sveltia-cms) setup for people who prefer a browser editor. It does not work out of the box: set `repo` in `admin/config.yml`, and provide GitHub authentication (for example a [Sveltia CMS Authenticator](https://github.com/sveltia/sveltia-cms-auth) worker as `base_url`). If you do not need it, delete `admin/`; the build does not depend on it.

## Deploying

Any static host works. For Cloudflare Pages, connect the repo and use:

- Build command: `python3 build.py`
- Output directory: `dist`

Or build locally and upload with `npx wrangler pages deploy dist --project-name your-project`.

## License

MIT. See [LICENSE](LICENSE).
