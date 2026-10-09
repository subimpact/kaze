/**
 * KAZE (風) - Client-side scripts
 * Lightweight, zero-dependency tactile interactions
 */
document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Drawer Navigation Toggle
  const toggleBtn = document.querySelector('.mobile-toggle');
  const drawer = document.querySelector('.mobile-drawer');

  if (toggleBtn && drawer) {
    toggleBtn.addEventListener('click', () => {
      const isOpen = drawer.classList.toggle('open');
      toggleBtn.setAttribute('aria-expanded', isOpen);
      drawer.setAttribute('aria-hidden', !isOpen);
    });

    // Close on navigation click
    const mobileLinks = drawer.querySelectorAll('a');
    mobileLinks.forEach((link) => {
      link.addEventListener('click', () => {
        drawer.classList.remove('open');
        toggleBtn.setAttribute('aria-expanded', 'false');
        drawer.setAttribute('aria-hidden', 'true');
      });
    });
  }

  // 2. Terminal Quickstart Code Copy
  const copyBtn = document.getElementById('copy-btn');
  const codeEl = document.getElementById('quickstart-code');

  if (copyBtn && codeEl) {
    copyBtn.addEventListener('click', async () => {
      const textToCopy = `git clone https://github.com/subimpact/kaze.git my-site\ncd my-site && python3 dev.py\npython3 build.py`;
      try {
        await navigator.clipboard.writeText(textToCopy);
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'COPIED!';
        copyBtn.style.backgroundColor = 'var(--accent)';
        copyBtn.style.color = '#ffffff';
        setTimeout(() => {
          copyBtn.textContent = originalText;
          copyBtn.style.backgroundColor = '';
          copyBtn.style.color = '';
        }, 2000);
      } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = textToCopy;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        copyBtn.textContent = 'COPIED!';
        setTimeout(() => {
          copyBtn.textContent = 'COPY';
        }, 2000);
      }
    });
  }

  // 3. Blog Category Filtering
  const filterBtns = document.querySelectorAll('.filter-btn');
  const articleCards = document.querySelectorAll('.blog-card');

  filterBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      filterBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.getAttribute('data-filter');
      articleCards.forEach((card) => {
        if (filter === 'all' || card.getAttribute('data-category') === filter) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });

  // 4. Contact Form Feedback
  const contactForm = document.getElementById('contact-form');
  const feedback = document.getElementById('form-feedback');

  if (contactForm && feedback) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'TRANSMITTING...';

      // Simulate client-side confirmation for static edge
      setTimeout(() => {
        feedback.textContent = 'Thank you. Your message has been received by the Kaze team.';
        feedback.style.color = 'var(--accent)';
        feedback.hidden = false;
        contactForm.reset();
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }, 600);
    });
  }
});
