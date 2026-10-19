document.addEventListener("DOMContentLoaded", () => {
  // Menu Mobile
  const mobileBtn = document.getElementById("mobileMenuBtn");
  const navLinks = document.getElementById("navLinks");
  if (mobileBtn && navLinks) {
    mobileBtn.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });
  }

  // Modal de Busca Rápida
  const openSearchBtn = document.getElementById("openSearchModal");
  const closeSearchBtn = document.getElementById("closeSearchModal");
  const searchModal = document.getElementById("searchModal");
  const searchInput = document.getElementById("searchModalInput");

  if (openSearchBtn && searchModal) {
    openSearchBtn.addEventListener("click", () => {
      searchModal.classList.add("open");
      if (searchInput) setTimeout(() => searchInput.focus(), 80);
    });
  }

  if (closeSearchBtn && searchModal) {
    closeSearchBtn.addEventListener("click", () => {
      searchModal.classList.remove("open");
    });
  }

  if (searchModal) {
    searchModal.addEventListener("click", (e) => {
      if (e.target === searchModal) searchModal.classList.remove("open");
    });
  }
});
