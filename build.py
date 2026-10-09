#!/usr/bin/env python3
"""
🍃 Kaze (風) - The Weightless Static Site Generator for Python
Zero external pip dependencies (100% Python standard library).
0.01s compilation into pure static HTML in dist/.
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

# --------------------------------------------------------------------------
# 1. Markdown to HTML Converter (Zero-dependency standard library)
# --------------------------------------------------------------------------

def markdown_to_html(md_text):
    """Converts basic Markdown to clean semantic HTML without external libraries."""
    if not md_text:
        return ""

    lines = md_text.strip().split('\n')
    html_blocks = []
    in_ul = False
    in_ol = False
    p_buffer = []

    def flush_p():
        nonlocal p_buffer
        if p_buffer:
            raw = ' '.join(p_buffer).strip()
            if raw:
                html_blocks.append(f"<p>{inline_format(raw)}</p>")
            p_buffer = []

    def flush_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_blocks.append("</ul>")
            in_ul = False
        if in_ol:
            html_blocks.append("</ol>")
            in_ol = False

    def inline_format(text):
        # Links: [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # Bold: **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # Italic: *text*
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        # Code: `code`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text

    for line in lines:
        stripped = line.strip()

        # Blank line triggers paragraph and list end
        if not stripped:
            flush_p()
            flush_lists()
            continue

        # Headings
        if stripped.startswith('### '):
            flush_p()
            flush_lists()
            html_blocks.append(f"<h3>{inline_format(stripped[4:])}</h3>")
            continue
        elif stripped.startswith('## '):
            flush_p()
            flush_lists()
            html_blocks.append(f"<h2>{inline_format(stripped[3:])}</h2>")
            continue
        elif stripped.startswith('# '):
            flush_p()
            flush_lists()
            html_blocks.append(f"<h1>{inline_format(stripped[2:])}</h1>")
            continue

        # Unordered list: - item or * item
        if stripped.startswith(('- ', '* ')):
            flush_p()
            if not in_ul:
                flush_lists()
                html_blocks.append("<ul>")
                in_ul = True
            html_blocks.append(f"<li>{inline_format(stripped[2:])}</li>")
            continue

        # Ordered list: 1. item
        m_ol = re.match(r'^\d+\.\s+(.+)$', stripped)
        if m_ol:
            flush_p()
            if not in_ol:
                flush_lists()
                html_blocks.append("<ol>")
                in_ol = True
            html_blocks.append(f"<li>{inline_format(m_ol.group(1))}</li>")
            continue

        # Blockquote: > text
        if stripped.startswith('> '):
            flush_p()
            flush_lists()
            html_blocks.append(f"<blockquote><p>{inline_format(stripped[2:])}</p></blockquote>")
            continue

        # Ordinary text -> accumulate into paragraph
        p_buffer.append(stripped)

    flush_p()
    flush_lists()
    return '\n'.join(html_blocks)


# --------------------------------------------------------------------------
# 2. Template Loader & Token Replacer
# --------------------------------------------------------------------------

def load_template(name):
    path = os.path.join(TEMPLATES_DIR, name)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def render(template_str, context):
    """Replaces {{key}} in template_str with str(value)."""
    result = template_str
    for key, val in context.items():
        placeholder = '{{' + key + '}}'
        result = result.replace(placeholder, str(val))
    return result

def write_page(rel_path, content):
    dest = os.path.join(DIST_DIR, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(content)


# --------------------------------------------------------------------------
# 3. Content Loaders
# --------------------------------------------------------------------------

def load_json(rel_path, default=None):
    path = os.path.join(CONTENT_DIR, rel_path)
    if not os.path.isfile(path):
        return default or {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  [ERROR] Malformed JSON in {rel_path}: {e}")
        return default or {}

def load_articles():
    art_dir = os.path.join(CONTENT_DIR, 'articles')
    articles = []
    if not os.path.isdir(art_dir):
        return articles
    for fn in sorted(os.listdir(art_dir)):
        if fn.endswith('.json'):
            data = load_json(os.path.join('articles', fn))
            if data and data.get('slug'):
                articles.append(data)
    # Sort newest first
    return sorted(articles, key=lambda a: a.get('date', ''), reverse=True)

def load_case_studies():
    cs_dir = os.path.join(CONTENT_DIR, 'case-studies')
    cases = []
    if not os.path.isdir(cs_dir):
        return cases
    for fn in sorted(os.listdir(cs_dir)):
        if fn.endswith('.json'):
            data = load_json(os.path.join('case-studies', fn))
            if data and data.get('slug'):
                cases.append(data)
    return cases


# --------------------------------------------------------------------------
# 4. Site Builder Core
# --------------------------------------------------------------------------

def build():
    t_start = time.time()
    print("🍃 Compiling KAZE (風)...")

    # Ensure output directories exist
    os.makedirs(DIST_DIR, exist_ok=True)

    # Copy static assets (CSS, JS, images, favicon)
    if os.path.isdir(STATIC_DIR):
        for item in os.listdir(STATIC_DIR):
            s = os.path.join(STATIC_DIR, item)
            d = os.path.join(DIST_DIR, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

    # Copy Sveltia CMS admin studio
    if os.path.isdir(ADMIN_DIR):
        admin_dest = os.path.join(DIST_DIR, 'admin')
        if os.path.exists(admin_dest):
            shutil.rmtree(admin_dest)
        shutil.copytree(ADMIN_DIR, admin_dest)

    # Load content
    site = load_json('site.json', {
        'name': 'Agency', 'short_name': 'Agency', 'tagline': 'PR & Comms',
        'url': 'https://example.com', 'description': 'Communications Consultancy',
        'contact': {}, 'nav': [], 'stats': [], 'services': []
    })
    team = load_json('team.json', {'members': []})
    articles = load_articles()
    cases = load_case_studies()

    # Load base partials
    base_tpl = load_template('base.html')
    header_tpl = load_template('header.html')
    footer_tpl = load_template('footer.html')

    # Common navigation links
    nav_links_html = ''.join(f'<a href="{item["url"]}">{html.escape(item["label"])}</a>' for item in site.get('nav', []))
    header_html = render(header_tpl, {
        'site_name': html.escape(site.get('name', '')),
        'site_short_name': html.escape(site.get('short_name', '')),
        'nav_links': nav_links_html,
        'mobile_nav_links': nav_links_html,
    })

    footer_html = render(footer_tpl, {
        'site_name': html.escape(site.get('name', '')),
        'site_short_name': html.escape(site.get('short_name', '')),
        'site_description': html.escape(site.get('description', '')),
        'contact_email': html.escape(site.get('contact', {}).get('email', '')),
        'contact_phone': html.escape(site.get('contact', {}).get('phone', '')),
        'current_year': time.strftime('%Y'),
    })

    def make_page(title, desc, canonical, content_html, extra_head="", og_image="/images/og.jpg"):
        ctx = {
            'title': f"{title} | {site.get('name', '')}",
            'description': html.escape(desc),
            'canonical_url': canonical,
            'og_image': og_image,
            'extra_head': extra_head,
            'header': header_html,
            'content': content_html,
            'footer': footer_html,
            'extra_scripts': ''
        }
        return render(base_tpl, ctx)

    # 4A. Build Homepage
    print("  • Building Home page...")
    stats_html = ''.join(
        f'<div class="stat-item"><div class="stat-value">{s["value"]}</div><div class="stat-label">{html.escape(s["label"])}</div></div>'
        for s in site.get('stats', [])
    )
    services_html = ''.join(
        f'''<div class="pillar-card">
             <div class="pillar-kanji">{html.escape(s.get("kanji", "風"))}</div>
             <h3 class="pillar-title">{html.escape(s["title"])}</h3>
             <p class="pillar-desc">{html.escape(s["description"])}</p>
           </div>'''
        for s in site.get('services', [])
    )
    featured_cases_html = ''.join(
        f'''<div class="showcase-card">
             <div class="showcase-header">
               <span class="client-badge">{html.escape(c.get("client", ""))}</span>
               <span class="value-badge">{html.escape(c.get("value", ""))}</span>
             </div>
             <h3 class="showcase-title"><a href="/case-studies/{c["slug"]}">{html.escape(c["title"])}</a></h3>
             <p class="showcase-desc">{html.escape(c.get("objective", "")[:140])}...</p>
             <a href="/case-studies/{c["slug"]}" class="showcase-link">Read Case Study &rarr;</a>
           </div>'''
        for c in cases[:3]
    )
    latest_articles_html = ''.join(
        f'''<div class="article-card blog-card" data-category="{html.escape(a.get("category", "Architecture"))}">
             <div class="article-card-header">
               <span class="category-tag">{html.escape(a.get("category", "Architecture"))}</span>
               <span class="article-read-tag">{a.get("read_min", 4)} min read</span>
             </div>
             <h3 class="article-card-title"><a href="/blog/{a["slug"]}">{html.escape(a["title"])}</a></h3>
             <p class="article-card-desc">{html.escape(a.get("excerpt", ""))}</p>
             <div class="article-card-footer">
               <span class="article-date">{a.get("date", "")}</span>
               <a href="/blog/{a["slug"]}" class="article-link">Read Guide &rarr;</a>
             </div>
           </div>'''
        for a in articles[:3]
    )

    home_content = render(load_template('index.html'), {
        'site_description': html.escape(site.get('description', '')),
        'stats_items': stats_html,
        'services_items': services_html,
        'featured_cases': featured_cases_html,
        'latest_articles': latest_articles_html,
    })
    write_page('index.html', make_page(site.get('name', 'Home'), site.get('description', ''), site.get('url', ''), home_content))

    # 4B. Build About Page
    print("  • Building About page...")
    team_cards_html = ''.join(
        f'''<div class="team-card">
             <div class="team-avatar">{m["name"][0]}</div>
             <h3 class="team-name">{html.escape(m["name"])}</h3>
             <div class="team-role">{html.escape(m["role"])}</div>
             <p class="team-bio">{html.escape(m.get("bio", ""))}</p>
           </div>'''
        for m in team.get('members', [])
    )
    about_content = render(load_template('about.html'), {
        'team_cards': team_cards_html,
    })
    write_page('about-us/index.html', make_page('About Us', 'Discover our communications philosophy and team leadership.', f"{site.get('url', '')}/about-us", about_content))

    # 4C. Build Contact Page
    print("  • Building Contact page...")
    contact_info = site.get('contact', {})
    contact_content = render(load_template('contact.html'), {
        'contact_email': html.escape(contact_info.get('email', '')),
        'contact_phone': html.escape(contact_info.get('phone', '')),
        'contact_address': html.escape(contact_info.get('address', '')),
        'contact_whatsapp': html.escape(contact_info.get('whatsapp', '')),
    })
    write_page('contact-us/index.html', make_page('Contact Us', 'Get in touch for communications counsel, media campaigns, and brand advisory.', f"{site.get('url', '')}/contact-us", contact_content))

    # 4D. Build Blog Archive & Articles
    print(f"  • Building Blog Archive ({len(articles)} articles)...")
    categories = sorted(list(set(a.get('category', 'Architecture') for a in articles if a.get('category'))))
    category_filters_html = ''.join(f'<button type="button" class="filter-btn" data-filter="{html.escape(c)}">{html.escape(c)}</button>' for c in categories)

    all_article_cards = ''.join(
        f'''<div class="article-card blog-card" data-category="{html.escape(a.get("category", "Architecture"))}">
             <div class="article-card-header">
               <span class="category-tag">{html.escape(a.get("category", "Architecture"))}</span>
               <span class="article-read-tag">{a.get("read_min", 4)} min read</span>
             </div>
             <h3 class="article-card-title"><a href="/blog/{a["slug"]}">{html.escape(a["title"])}</a></h3>
             <p class="article-card-desc">{html.escape(a.get("excerpt", ""))}</p>
             <div class="article-card-footer">
               <span class="article-date">{a.get("date", "")}</span>
               <a href="/blog/{a["slug"]}" class="article-link">Read Guide &rarr;</a>
             </div>
           </div>'''
        for a in articles
    )
    blog_list_content = render(load_template('blog-list.html'), {
        'category_filters': category_filters_html,
        'article_cards': all_article_cards,
    })
    write_page('blog/index.html', make_page('Architecture & Guides', 'Technical documentation and guides on the weightless Python static site generator.', f"{site.get('url', '')}/blog", blog_list_content))

    # Individual Articles
    blog_post_tpl = load_template('blog-post.html')
    for a in articles:
        faq_items = a.get('faq', [])
        faq_html = ""
        if faq_items:
            faq_rows = ''.join(
                f'<div class="faq-item"><div class="faq-question">{html.escape(item["q"])}</div><div class="faq-answer">{html.escape(item["a"])}</div></div>'
                for item in faq_items
            )
            faq_html = f'''<div class="faq-container"><h2>Frequently Asked Questions</h2>{faq_rows}</div>'''

        post_body_html = markdown_to_html(a.get('body', ''))
        post_content = render(blog_post_tpl, {
            'title': html.escape(a.get('title', '')),
            'excerpt': html.escape(a.get('excerpt', '')),
            'category': html.escape(a.get('category', 'PR')),
            'author': html.escape(a.get('author', 'Strategist')),
            'date': a.get('date', ''),
            'date_formatted': a.get('date', ''),
            'read_min': a.get('read_min', 5),
            'body_html': post_body_html,
            'faq_section': faq_html,
        })

        # Schema.org JSON-LD
        ld_json = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": a.get('title', ''),
            "description": a.get('excerpt', ''),
            "author": {"@type": "Person", "name": a.get('author', '')},
            "datePublished": a.get('date', ''),
            "mainEntityOfPage": f"{site.get('url', '')}/blog/{a['slug']}"
        }
        extra_head = f'<script type="application/ld+json">{json.dumps(ld_json)}</script>'

        write_page(f"blog/{a['slug']}/index.html", make_page(
            a.get('title', ''), a.get('excerpt', ''), f"{site.get('url', '')}/blog/{a['slug']}",
            post_content, extra_head=extra_head
        ))

    # 4E. Build Case Studies Archive & Individual Cases
    print(f"  • Building Case Studies ({len(cases)} cases)...")
    cases_cards_html = ''.join(
        f'''<div class="showcase-card">
             <div class="showcase-header">
               <span class="client-badge">{html.escape(c.get("client", ""))}</span>
               <span class="value-badge">{html.escape(c.get("value", ""))}</span>
             </div>
             <h3 class="showcase-title"><a href="/case-studies/{c["slug"]}">{html.escape(c["title"])}</a></h3>
             <p class="showcase-desc">{html.escape(c.get("objective", ""))}</p>
             <a href="/case-studies/{c["slug"]}" class="showcase-link">Read Case Study &rarr;</a>
           </div>'''
        for c in cases
    )
    cases_archive_content = f'''<section class="page-hero">
      <div class="kanji-watermark" aria-hidden="true">証</div>
      <div class="container page-hero-inner">
        <div class="hero-tag-wrap"><span class="eyebrow-tag">PRODUCTION SHOWCASE</span></div>
        <h1 class="page-title">Documented Benchmarks & Case Studies</h1>
        <p class="page-lead">Measurable performance metrics from production deployments powered by Kaze.</p>
      </div>
    </section>
    <section class="section"><div class="container"><div class="showcase-grid">{cases_cards_html}</div></div></section>'''
    write_page('case-studies/index.html', make_page('Showcase & Benchmarks', 'Explore documented production benchmarks and speed gains with Kaze.', f"{site.get('url', '')}/case-studies", cases_archive_content))

    # Individual Case Studies
    case_tpl = load_template('case-study.html')
    for c in cases:
        results_items_html = ''.join(f'<li>{html.escape(r)}</li>' for r in c.get('results', []))
        case_content = render(case_tpl, {
            'title': html.escape(c.get('title', '')),
            'client': html.escape(c.get('client', '')),
            'value': html.escape(c.get('value', '')),
            'objective': html.escape(c.get('objective', '')),
            'results_items': results_items_html,
        })
        write_page(f"case-studies/{c['slug']}/index.html", make_page(
            c.get('title', ''), c.get('objective', ''), f"{site.get('url', '')}/case-studies/{c['slug']}",
            case_content
        ))

    # 4F. Automated Sitemap.xml
    print("  • Generating sitemap.xml...")
    site_url = site.get('url', 'https://example.com').rstrip('/')
    urls = [
        (f"{site_url}/", '1.0'),
        (f"{site_url}/about-us", '0.8'),
        (f"{site_url}/contact-us", '0.8'),
        (f"{site_url}/case-studies", '0.8'),
        (f"{site_url}/blog", '0.8'),
    ]
    for c in cases:
        urls.append((f"{site_url}/case-studies/{c['slug']}", '0.7'))
    for a in articles:
        urls.append((f"{site_url}/blog/{a['slug']}", '0.6'))

    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    today = time.strftime('%Y-%m-%d')
    for loc, prio in urls:
        sitemap_lines.append(f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><priority>{prio}</priority></url>')
    sitemap_lines.append('</urlset>')

    write_page('sitemap.xml', '\n'.join(sitemap_lines) + '\n')

    duration = time.time() - t_start
    print(f"✨ Build Complete! {len(urls)} URLs compiled in {duration:.2f}s into dist/\n")

if __name__ == '__main__':
    build()
