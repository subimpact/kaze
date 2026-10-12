#!/usr/bin/env python3
"""
Kaze (風) - a small static site generator in one Python file.

Standard library only. Reads JSON content from content/, fills HTML templates
from templates/, and writes a static site to dist/.

Kaze is deliberately small. It ships a fixed set of page types (home, about,
contact, articles, case studies) aimed at agency and small-business sites.
If you need arbitrary routing, a plugin system, or a large theme ecosystem,
use Hugo, Pelican, Eleventy, or Astro instead.
"""

import os
import sys
import json
import html
import re
import shutil
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, 'content')
TEMPLATES_DIR = os.path.join(ROOT, 'templates')
STATIC_DIR = os.path.join(ROOT, 'static')
ADMIN_DIR = os.path.join(ROOT, 'admin')
DIST_DIR = os.path.join(ROOT, 'dist')

WARNINGS = []


# --------------------------------------------------------------------------
# 1. Markdown to HTML
#
# Supported: # to #### headings, paragraphs, **bold**, *italic*, `code`,
# [links](url), fenced ``` code blocks, - / * / 1. lists (one level),
# > blockquotes, and --- horizontal rules.
# Not supported: nested lists, tables, images, footnotes.
# Raw HTML in markdown is escaped, not rendered.
# --------------------------------------------------------------------------

def inline_format(text):
    """Escape text, then apply inline markdown. Code spans are protected."""
    parts = re.split(r'(`[^`]+`)', text)
    out = []
    for part in parts:
        if len(part) > 1 and part.startswith('`') and part.endswith('`'):
            out.append(f"<code>{html.escape(part[1:-1])}</code>")
            continue
        s = html.escape(part)
        s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', s)
        s = re.sub(r'\*\*(?=\S)(.+?)(?<=\S)\*\*', r'<strong>\1</strong>', s)
        # Single * only counts as emphasis when not inside a word (so 2*3*4 stays as is)
        s = re.sub(r'(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])', r'<em>\1</em>', s)
        out.append(s)
    return ''.join(out)


def markdown_to_html(md_text):
    if not md_text:
        return ""

    lines = md_text.replace('\r\n', '\n').split('\n')
    blocks = []
    para = []
    list_type = None   # 'ul' or 'ol'
    in_code = False
    code_lang = ''
    code_lines = []

    def flush_para():
        nonlocal para
        if para:
            blocks.append(f"<p>{inline_format(' '.join(para).strip())}</p>")
            para = []

    def close_list():
        nonlocal list_type
        if list_type:
            blocks.append(f"</{list_type}>")
            list_type = None

    for line in lines:
        stripped = line.strip()

        # Fenced code blocks
        if stripped.startswith('```'):
            if in_code:
                cls = f' class="language-{html.escape(code_lang)}"' if code_lang else ''
                blocks.append(f"<pre><code{cls}>{html.escape(chr(10).join(code_lines))}</code></pre>")
                in_code, code_lang, code_lines = False, '', []
            else:
                flush_para()
                close_list()
                in_code = True
                code_lang = stripped[3:].strip()
            continue
        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_para()
            close_list()
            continue

        m_h = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if m_h:
            flush_para()
            close_list()
            level = len(m_h.group(1))
            blocks.append(f"<h{level}>{inline_format(m_h.group(2))}</h{level}>")
            continue

        if re.match(r'^(-{3,}|\*{3,})$', stripped):
            flush_para()
            close_list()
            blocks.append("<hr />")
            continue

        m_ul = re.match(r'^[-*]\s+(.+)$', stripped)
        m_ol = re.match(r'^\d+\.\s+(.+)$', stripped)
        if m_ul or m_ol:
            flush_para()
            wanted = 'ul' if m_ul else 'ol'
            if list_type != wanted:
                close_list()
                blocks.append(f"<{wanted}>")
                list_type = wanted
            blocks.append(f"<li>{inline_format((m_ul or m_ol).group(1))}</li>")
            continue

        if stripped.startswith('> '):
            flush_para()
            close_list()
            blocks.append(f"<blockquote><p>{inline_format(stripped[2:])}</p></blockquote>")
            continue

        close_list()
        para.append(stripped)

    if in_code:  # unclosed fence: still output what we have
        blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    flush_para()
    close_list()
    # Escape braces so literal {{text}} in content is never treated as a placeholder
    return '\n'.join(blocks).replace('{', '&#123;')


# --------------------------------------------------------------------------
# 2. Templates
#
# {{key}}                          replaced with a value
# <!-- if:flag --> ... <!-- endif:flag -->   kept only when flag is truthy
# --------------------------------------------------------------------------

def load_template(name):
    with open(os.path.join(TEMPLATES_DIR, name), 'r', encoding='utf-8') as f:
        return f.read()


def apply_conditionals(template_str, flags):
    def repl(m):
        return m.group(2) if flags.get(m.group(1)) else ''
    return re.sub(r'<!-- if:(\w+) -->(.*?)<!-- endif:\1 -->', repl, template_str, flags=re.DOTALL)


def render(template_str, context, flags=None):
    result = apply_conditionals(template_str, flags or {})
    for key, val in context.items():
        result = result.replace('{{' + key + '}}', str(val))
    return result


def write_page(rel_path, content):
    leftovers = sorted(set(re.findall(r'\{\{\s*[\w.]+\s*\}\}', content)))
    if leftovers:
        WARNINGS.append(f"{rel_path}: unfilled placeholders {', '.join(leftovers)}")
    dest = os.path.join(DIST_DIR, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(content)


# --------------------------------------------------------------------------
# 3. Content
# --------------------------------------------------------------------------

def load_json(rel_path, default=None):
    path = os.path.join(CONTENT_DIR, rel_path)
    if not os.path.isfile(path):
        return default if default is not None else {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # Fail the build instead of silently dropping content on CI
        print(f"  [ERROR] Malformed JSON in content/{rel_path}: {e}")
        sys.exit(1)


def load_collection(folder):
    col_dir = os.path.join(CONTENT_DIR, folder)
    items = []
    if not os.path.isdir(col_dir):
        return items
    for fn in sorted(os.listdir(col_dir)):
        if fn.endswith('.json'):
            data = load_json(os.path.join(folder, fn))
            if data and data.get('slug'):
                items.append(data)
            else:
                WARNINGS.append(f"content/{folder}/{fn}: skipped (missing slug)")
    return items


def esc(value):
    # Braces are escaped too, so content can never be mistaken for a {{placeholder}}
    return html.escape(str(value), quote=True).replace('{', '&#123;')


# --------------------------------------------------------------------------
# 4. Build
# --------------------------------------------------------------------------

DEFAULT_PAGES = {
    'about': {'title': 'About', 'description': 'About us.'},
    'contact': {'title': 'Contact', 'description': 'Get in touch.'},
    'blog': {'title': 'Articles', 'description': 'Articles and guides.'},
    'case_studies': {'title': 'Case Studies', 'description': 'Selected work.'},
}


def article_card(a):
    cat = esc(a.get('category', 'General'))
    return f'''<div class="article-card blog-card" data-category="{cat}">
  <div class="article-card-header">
    <span class="category-tag">{cat}</span>
    <span class="article-read-tag">{esc(a.get("read_min", 4))} min read</span>
  </div>
  <h3 class="article-card-title"><a href="/blog/{esc(a["slug"])}">{esc(a["title"])}</a></h3>
  <p class="article-card-desc">{esc(a.get("excerpt", ""))}</p>
  <div class="article-card-footer">
    <span class="article-date">{esc(a.get("date", ""))}</span>
    <a href="/blog/{esc(a["slug"])}" class="article-link">Read &rarr;</a>
  </div>
</div>'''


def case_card(c, short=False):
    objective = c.get('objective', '')
    if short and len(objective) > 140:
        objective = objective[:140].rsplit(' ', 1)[0] + '...'
    return f'''<div class="showcase-card">
  <div class="showcase-header">
    <span class="client-badge">{esc(c.get("client", ""))}</span>
    <span class="value-badge">{esc(c.get("value", ""))}</span>
  </div>
  <h3 class="showcase-title"><a href="/case-studies/{esc(c["slug"])}">{esc(c["title"])}</a></h3>
  <p class="showcase-desc">{esc(objective)}</p>
  <a href="/case-studies/{esc(c["slug"])}" class="showcase-link">Read case study &rarr;</a>
</div>'''


def build():
    t_start = time.time()
    WARNINGS.clear()
    print("Building Kaze site...")

    # Start from an empty dist/ so deleted content never lingers
    if os.path.isdir(DIST_DIR) and os.path.dirname(DIST_DIR) == ROOT:
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)

    if os.path.isdir(STATIC_DIR):
        shutil.copytree(STATIC_DIR, DIST_DIR, dirs_exist_ok=True)
    if os.path.isdir(ADMIN_DIR):
        shutil.copytree(ADMIN_DIR, os.path.join(DIST_DIR, 'admin'))

    site = load_json('site.json', {'name': 'My Site', 'url': 'https://example.com'})
    team = load_json('team.json', {'members': []})
    articles = sorted(load_collection('articles'), key=lambda a: a.get('date', ''), reverse=True)
    cases = load_collection('case-studies')
    pages = {k: {**v, **site.get('pages', {}).get(k, {})} for k, v in DEFAULT_PAGES.items()}
    site_url = site.get('url', 'https://example.com').rstrip('/')

    base_tpl = load_template('base.html')
    nav_html = ''.join(f'<a href="{esc(i["url"])}">{esc(i["label"])}</a>' for i in site.get('nav', []))
    header_html = render(load_template('header.html'), {
        'site_name': esc(site.get('name', '')),
        'site_short_name': esc(site.get('short_name', '')),
        'nav_links': nav_html,
        'mobile_nav_links': nav_html,
    })
    footer_html = render(load_template('footer.html'), {
        'site_name': esc(site.get('name', '')),
        'site_short_name': esc(site.get('short_name', '')),
        'site_description': esc(site.get('description', '')),
        'contact_email': esc(site.get('contact', {}).get('email', '')),
        'current_year': time.strftime('%Y'),
    })

    og_path = site.get('og_image', '')
    og_exists = og_path and os.path.isfile(os.path.join(STATIC_DIR, og_path.lstrip('/')))
    if og_path and not og_exists:
        WARNINGS.append(f"og_image {og_path} not found in static/, skipping og:image tags")

    def make_page(title, desc, path, content_html, extra_head=""):
        og_meta = ''
        if og_exists:
            og_meta = (f'<meta property="og:image" content="{esc(site_url + og_path)}" />\n'
                       f'  <meta name="twitter:image" content="{esc(site_url + og_path)}" />')
        full_title = site.get('name', '') if title == site.get('name') else f"{title} | {site.get('name', '')}"
        return render(base_tpl, {
            'title': esc(full_title),
            'description': esc(desc),
            'canonical_url': esc(site_url + path),
            'og_meta': og_meta,
            'extra_head': extra_head,
            'header': header_html,
            'content': content_html,
            'footer': footer_html,
            'extra_scripts': '',
        })

    sitemap = []  # (path, lastmod)
    today = time.strftime('%Y-%m-%d')

    # Home
    print("  - home")
    stats_html = ''.join(
        f'<div class="stat-item"><div class="stat-value">{esc(s["value"])}</div>'
        f'<div class="stat-label">{esc(s["label"])}</div></div>'
        for s in site.get('stats', [])
    )
    services_html = ''.join(
        f'''<div class="pillar-card">
  <div class="pillar-kanji">{esc(s.get("kanji", ""))}</div>
  <h3 class="pillar-title">{esc(s["title"])}</h3>
  <p class="pillar-desc">{esc(s["description"])}</p>
</div>'''
        for s in site.get('services', [])
    )
    home_content = render(load_template('index.html'), {
        'site_description': esc(site.get('description', '')),
        'stats_items': stats_html,
        'services_items': services_html,
        'featured_cases': ''.join(case_card(c, short=True) for c in cases[:3]),
        'latest_articles': ''.join(article_card(a) for a in articles[:3]),
    }, flags={'cases': bool(cases), 'articles': bool(articles), 'stats': bool(stats_html)})
    write_page('index.html', make_page(site.get('name', 'Home'), site.get('description', ''), '/', home_content))
    sitemap.append(('/', today))

    # About
    print("  - about")
    team_html = ''.join(
        f'''<div class="team-card">
  <div class="team-avatar">{esc(m["name"][:1])}</div>
  <h3 class="team-name">{esc(m["name"])}</h3>
  <div class="team-role">{esc(m.get("role", ""))}</div>
  <p class="team-bio">{esc(m.get("bio", ""))}</p>
</div>'''
        for m in team.get('members', [])
    )
    about = render(load_template('about.html'), {'team_cards': team_html}, flags={'team': bool(team_html)})
    write_page('about-us/index.html', make_page(pages['about']['title'], pages['about']['description'], '/about-us', about))
    sitemap.append(('/about-us', today))

    # Contact
    print("  - contact")
    contact = site.get('contact', {})
    contact_html = render(load_template('contact.html'), {
        'contact_email': esc(contact.get('email', '')),
        'github_url': esc(site.get('github_url', '')),
    }, flags={'email': bool(contact.get('email')), 'github': bool(site.get('github_url'))})
    write_page('contact-us/index.html', make_page(pages['contact']['title'], pages['contact']['description'], '/contact-us', contact_html))
    sitemap.append(('/contact-us', today))

    # Articles
    if articles:
        print(f"  - articles ({len(articles)})")
        categories = sorted({a.get('category', 'General') for a in articles})
        filters = ''.join(f'<button type="button" class="filter-btn" data-filter="{esc(c)}">{esc(c)}</button>' for c in categories)
        blog_list = render(load_template('blog-list.html'), {
            'category_filters': filters,
            'article_cards': ''.join(article_card(a) for a in articles),
        })
        write_page('blog/index.html', make_page(pages['blog']['title'], pages['blog']['description'], '/blog', blog_list))
        sitemap.append(('/blog', today))

        post_tpl = load_template('blog-post.html')
        for a in articles:
            faq = a.get('faq', [])
            faq_html = ''
            ld = [{
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": a.get('title', ''),
                "description": a.get('excerpt', ''),
                "author": {"@type": "Person", "name": a.get('author', '')},
                "datePublished": a.get('date', ''),
                "mainEntityOfPage": f"{site_url}/blog/{a['slug']}",
            }]
            if faq:
                rows = ''.join(
                    f'<div class="faq-item"><h3 class="faq-question">{esc(i["q"])}</h3>'
                    f'<p class="faq-answer">{esc(i["a"])}</p></div>'
                    for i in faq
                )
                faq_html = f'<section class="faq-container"><h2>Frequently asked questions</h2>{rows}</section>'
                ld.append({
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    "mainEntity": [{"@type": "Question", "name": i["q"],
                                    "acceptedAnswer": {"@type": "Answer", "text": i["a"]}} for i in faq],
                })
            # Backslash kept out of the f-string so this runs on Python < 3.12
            safe_ld = [json.dumps(obj).replace('</', '<\\/').replace('{{', '{\\u007b') for obj in ld]
            extra_head = ''.join(f'<script type="application/ld+json">{s}</script>' for s in safe_ld)
            post = render(post_tpl, {
                'title': esc(a.get('title', '')),
                'excerpt': esc(a.get('excerpt', '')),
                'category': esc(a.get('category', 'General')),
                'author': esc(a.get('author', '')),
                'date': esc(a.get('date', '')),
                'date_formatted': esc(a.get('date', '')),
                'read_min': esc(a.get('read_min', 4)),
                'body_html': markdown_to_html(a.get('body', '')),
                'faq_section': faq_html,
            })
            write_page(f"blog/{a['slug']}/index.html",
                       make_page(a.get('title', ''), a.get('excerpt', ''), f"/blog/{a['slug']}", post, extra_head))
            sitemap.append((f"/blog/{a['slug']}", a.get('date') or today))

    # Case studies
    if cases:
        print(f"  - case studies ({len(cases)})")
        archive = render(load_template('case-list.html'), {
            'case_cards': ''.join(case_card(c) for c in cases),
            'page_title': esc(pages['case_studies']['title']),
            'page_lead': esc(pages['case_studies']['description']),
        })
        write_page('case-studies/index.html',
                   make_page(pages['case_studies']['title'], pages['case_studies']['description'], '/case-studies', archive))
        sitemap.append(('/case-studies', today))

        case_tpl = load_template('case-study.html')
        for c in cases:
            body = render(case_tpl, {
                'title': esc(c.get('title', '')),
                'client': esc(c.get('client', '')),
                'value': esc(c.get('value', '')),
                'objective': esc(c.get('objective', '')),
                'results_items': ''.join(f'<li>{esc(r)}</li>' for r in c.get('results', [])),
            })
            write_page(f"case-studies/{c['slug']}/index.html",
                       make_page(c.get('title', ''), c.get('objective', ''), f"/case-studies/{c['slug']}", body))
            sitemap.append((f"/case-studies/{c['slug']}", today))

    # 404 page (static hosts such as Cloudflare Pages serve 404.html for unknown paths)
    if os.path.isfile(os.path.join(TEMPLATES_DIR, '404.html')):
        page = make_page('Page not found', 'This page does not exist.', '/404', render(load_template('404.html'), {}))
        write_page('404.html', page.replace('<head>', '<head>\n  <meta name="robots" content="noindex" />', 1))

    # Sitemap
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines += [f'  <url><loc>{esc(site_url + p)}</loc><lastmod>{esc(d)}</lastmod></url>' for p, d in sitemap]
    lines.append('</urlset>')
    write_page('sitemap.xml', '\n'.join(lines) + '\n')

    for w in WARNINGS:
        print(f"  [WARN] {w}")
    print(f"Done: {len(sitemap)} pages in {time.time() - t_start:.3f}s -> dist/\n")


if __name__ == '__main__':
    build()
