/**
 * Kaze - small client-side helpers: mobile menu, copy button, article filters.
 */
document.addEventListener('DOMContentLoaded', () => {
  // Mobile drawer
  const toggleBtn = document.querySelector('.mobile-toggle');
  const drawer = document.querySelector('.mobile-drawer');
  if (toggleBtn && drawer) {
    const setOpen = (open) => {
      drawer.classList.toggle('open', open);
      toggleBtn.setAttribute('aria-expanded', String(open));
      drawer.setAttribute('aria-hidden', String(!open));
    };
    toggleBtn.addEventListener('click', () => setOpen(!drawer.classList.contains('open')));
    drawer.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setOpen(false)));
  }

  // Copy quickstart commands (comment lines are skipped)
  const copyBtn = document.getElementById('copy-btn');
  const codeEl = document.getElementById('quickstart-code');
  if (copyBtn && codeEl) {
    copyBtn.addEventListener('click', async () => {
      const text = codeEl.innerText
        .split('\n')
        .filter((line) => line.trim() && !line.trim().startsWith('#'))
        .join('\n');
      try {
        await navigator.clipboard.writeText(text);
        copyBtn.textContent = 'Copied';
      } catch (err) {
        copyBtn.textContent = 'Copy failed';
      }
      setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
    });
  }

  // Article category filters
  const filterBtns = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('.blog-card');
  filterBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      filterBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.getAttribute('data-filter');
      cards.forEach((card) => {
        card.style.display = (filter === 'all' || card.getAttribute('data-category') === filter) ? '' : 'none';
      });
    });
  });
});
