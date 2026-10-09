# 🍃 Kaze (風)

**The Weightless Static Site Generator for Python.**

*Go has Hugo. Rust has Zola. Ruby has Jekyll. Python has Kaze.*

Kaze (風, meaning *Wind*) is an ultra-fast, zero-dependency static site generator designed for marketing, PR, and editorial agency sites.

---

## ⚡ Why Kaze?

| Traditional Frameworks (Next.js / Astro / WordPress) | 🍃 Kaze (風) |
|---|---|
| 800+ nested `node_modules` that break on updates | **Zero external dependencies** (100% Python standard library) |
| 45–90s build times on CI | **0.01s instant compilation** |
| Complex headless CMS subscriptions ($50–$200/mo) | **Decoupled file-based content (edit in VS Code, Obsidian, or Sveltia CMS)** |
| Database vulnerabilities & plugin bloat | **100% static HTML, CDN edge cached, unhackable** |
| Vendor lock-in & proprietary schemas | **Pure standard JSON/Markdown files + plain HTML templates** |

---

## 📁 Directory Architecture

```text
kaze/
├── content/                     # All site data (edited via Sveltia CMS or code)
│   ├── site.json                # Brand identity, navigation, stats, services, contact
│   ├── team.json                # Leadership & team member bios
│   ├── articles/                # Insights / Blog posts (.json)
│   └── case-studies/            # Client work & PR results (.json)
├── templates/                   # Clean HTML templates (simple token replacement)
│   ├── base.html                # HTML5 shell, OpenGraph, fonts, layout
│   ├── header.html              # Sticky navigation & mobile drawer
│   ├── footer.html              # Footer columns, contact, copyright
│   ├── index.html               # Homepage layout
│   ├── about.html               # About & team roster layout
│   ├── contact.html             # Contact info & inquiry form
│   ├── blog-list.html           # Articles archive with category filters
│   ├── blog-post.html           # Article post layout with FAQ accordion & schema
│   └── case-study.html          # Case study layout with PR valuation badges
├── static/                      # Static assets copied into dist/ on build
│   ├── css/style.css            # Taste-skill responsive CSS design system
│   ├── js/main.js               # Mobile menu, category filters, FAQ accordion
│   └── images/                  # Client logos, headshots, thumbnails
├── admin/                       # Optional Sveltia / Decap CMS visual studio
│   ├── index.html               # CMS single-page web app (zero-install)
│   └── config.yml               # Decap/Sveltia open-standard collection schema
├── build.py                     # The Kaze compiler (compiles content + templates into dist/)
├── dev.py                       # Local live-reload development server
└── dist/                        # Production-ready compiled output
```

---

## 🚀 5-Minute Quickstart

### 1. Clone & Customize Brand
```bash
git clone https://github.com/subimpact/kaze.git my-site
cd my-site
```
Edit `content/site.json` to configure your brand name, contact info, and navigation:
```json
{
  "name": "Acme Agency",
  "short_name": "Acme",
  "tagline": "Strategic Communications & PR",
  "url": "https://example.com"
}
```

### 2. Run Local Dev Server
```bash
python3 dev.py
```
Open **`http://localhost:8000`** in your browser. Any change to `content/`, `templates/`, or `static/` triggers an instant rebuild.

### 3. Editorial Workflow (No CMS Lock-In)
Kaze is **100% file-based**. The compiler (`build.py`) has zero dependency on any CMS:
- **Developers / Technical Writers:** Edit JSON and Markdown files directly in VS Code, Obsidian, or your favorite editor. Push to Git, and your site deploys.
- **Client / Non-Technical Editors (Optional Visual CMS):** Kaze includes a pre-configured [Sveltia CMS](https://github.com/sveltia/sveltia-cms) studio at `/admin/`. Sveltia is a modern, lightweight Git-based CMS that commits directly to your repository with $0 SaaS fees. To enable it for production Git commits, point `base_url` in `admin/config.yml` to your GitHub OAuth worker (or deploy to Netlify). If you don't need a browser CMS, simply delete the `/admin/` folder.

### 4. Deploy to Cloudflare Pages (or Any Static Host)
1. Push your repository to GitHub.
2. In Cloudflare Dashboard → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**:
   - **Build command:** `python3 build.py`
   - **Build output directory:** `dist`
3. Hit **Save and Deploy**. Your site builds in milliseconds and is served globally at the edge.

---

## 🎨 Design System

All styling is managed in `static/css/style.css` via clean CSS variables:
```css
:root {
  --primary: #0C77B3;          /* Main brand accent */
  --primary-hover: #095c8a;    /* Button hover state */
  --font-sans: 'Plus Jakarta Sans', system-ui, sans-serif;
  --radius-md: 10px;           /* Card border radius */
}
```
Swap `--primary` and the Google Fonts link in `templates/base.html` to re-theme the entire website in under 60 seconds.

---

## 🔍 Built-in SEO & Rich Results

Kaze automatically outputs:
1. **Dynamic `sitemap.xml`:** Generates clean URLs and priorities for all static pages, case studies, and blog posts with automatic date stamps.
2. **Article JSON-LD:** Structured schema on all articles for Google Rich Results.
3. **FAQPage JSON-LD:** Automatically turns FAQ entries into search-engine FAQ snippets.
4. **Open Graph & Twitter Cards:** Pre-filled with article excerpts and featured images.
