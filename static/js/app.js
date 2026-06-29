// Business Partnership — app.js
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 5s
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });
});
