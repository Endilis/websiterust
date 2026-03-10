// Mobile Menu Controller for RustInfo Website
(function() {
  'use strict';
  
  // Wait for DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    initMobileMenu();
  });
  
  function initMobileMenu() {
    // Get or create mobile menu elements
    const header = document.querySelector('header');
    const nav = document.querySelector('.nav');
    
    if (!header || !nav) return;
    
    // Create mobile menu toggle button
    const toggleBtn = createToggleButton();
    
    // Create mobile menu overlay
    const overlay = createMobileOverlay();
    
    // Insert elements
    const navRightSide = nav.querySelector('div:last-child');
    if (navRightSide) {
      navRightSide.appendChild(toggleBtn);
    }
    document.body.appendChild(overlay);
    
    // Add event listeners
    toggleBtn.addEventListener('click', toggleMenu);
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) {
        closeMenu();
      }
    });
    
    // Close menu on link click
    const mobileLinks = overlay.querySelectorAll('.link');
    mobileLinks.forEach(link => {
      link.addEventListener('click', closeMenu);
    });
    
    // Close menu on ESC key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && overlay.classList.contains('active')) {
        closeMenu();
      }
    });
    
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function() {
        if (window.innerWidth > 900 && overlay.classList.contains('active')) {
          closeMenu();
        }
      }, 250);
    });
    
    function toggleMenu() {
      const isActive = toggleBtn.classList.contains('active');
      if (isActive) {
        closeMenu();
      } else {
        openMenu();
      }
    }
    
    function openMenu() {
      toggleBtn.classList.add('active');
      overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      
      // Accessibility
      toggleBtn.setAttribute('aria-expanded', 'true');
      overlay.setAttribute('aria-hidden', 'false');
    }
    
    function closeMenu() {
      toggleBtn.classList.remove('active');
      overlay.classList.remove('active');
      document.body.style.overflow = '';
      
      // Accessibility
      toggleBtn.setAttribute('aria-expanded', 'false');
      overlay.setAttribute('aria-hidden', 'true');
    }
  }
  
  function createToggleButton() {
    const btn = document.createElement('button');
    btn.className = 'mobile-menu-toggle';
    btn.setAttribute('aria-label', 'Toggle mobile menu');
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = `
      <span></span>
      <span></span>
      <span></span>
    `;
    return btn;
  }
  
  function createMobileOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'mobile-menu-overlay';
    overlay.setAttribute('aria-hidden', 'true');
    
    // Clone navigation elements
    const navLinks = document.querySelector('.nav .links');
    const langSwitcher = document.querySelector('.nav .lang-switcher');
    
    const content = document.createElement('div');
    content.className = 'mobile-menu-content';
    
    if (navLinks) {
      const clonedLinks = navLinks.cloneNode(true);
      content.appendChild(clonedLinks);
    }
    
    if (langSwitcher) {
      const clonedLang = langSwitcher.cloneNode(true);
      content.appendChild(clonedLang);
    }
    
    overlay.appendChild(content);
    return overlay;
  }
})();
