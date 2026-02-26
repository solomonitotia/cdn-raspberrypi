// Storage bar
fetch('/api/stats/')
  .then(r => r.json())
  .then(data => {
    const bar  = document.getElementById('storage-bar');
    const text = document.getElementById('storage-text');
    const label = document.getElementById('storage-label');
    if (!bar) return;
    const pct = data.disk_total > 0
      ? Math.min(100, (data.disk_used / data.disk_total) * 100)
      : 0;
    bar.style.width = pct + '%';
    bar.style.background = pct > 85 ? '#ef4444' : pct > 65 ? '#f59e0b' : '#2563eb';
    text.textContent = formatBytes(data.disk_used) + ' / ' + formatBytes(data.disk_total);
    // Show drive path as tooltip / label if it's an external drive
    if (label && data.media_path && data.media_path !== '/var/cdn-media') {
      const parts = data.media_path.split('/');
      const driveName = parts[2] || 'external';  // /media/<name>/...
      label.textContent = '💾 ' + driveName.toUpperCase();
      label.title = data.media_path;
    }
  })
  .catch(() => {
    const text = document.getElementById('storage-text');
    if (text) text.textContent = '—';
  });

function formatBytes(b) {
  if (!b) return '0 B';
  const u = ['B','KB','MB','GB'];
  let i = 0;
  while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
  return b.toFixed(1) + ' ' + u[i];
}

// Theme Toggle
(function() {
  const themeToggle = document.getElementById('theme-toggle');
  const html = document.documentElement;

  // Load saved theme or detect system preference
  const savedTheme = localStorage.getItem('theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

  // Apply initial theme
  html.setAttribute('data-theme', initialTheme);

  // Toggle theme on button click
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = html.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

      html.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);

      // Add a subtle animation
      themeToggle.style.transform = 'scale(0.9)';
      setTimeout(() => {
        themeToggle.style.transform = '';
      }, 150);
    });
  }

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    }
  });
})();
