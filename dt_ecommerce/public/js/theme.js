document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.querySelector(".dt-navbar");
  const dropdown = document.querySelector(".dt-main-menu");
  const trigger = dropdown?.querySelector(".dt-menu-trigger");
  const screenSize = window.innerWidth;

  const searchTrigger = document.querySelector(".dt-search-trigger");
  const searchBox = document.querySelector(".dt-navbar-center");

  // Scroll effect
  window.addEventListener("scroll", () => {
    navbar?.classList.toggle("dt-navbar-scrolled", window.scrollY > 10);
  });

  // MENU TOGGLE (🔥 fix here)
  if (trigger && dropdown) {
    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.classList.toggle("open");
    });
  }

  // SEARCH TOGGLE
  if (searchTrigger && searchBox) {
    searchTrigger.addEventListener("click", (e) => {
      e.stopPropagation();
      searchBox.classList.toggle("open");

      setTimeout(() => {
        searchBox.querySelector("input")?.focus();
      }, 50);
    });


    let debounceTimer = null;
    const input = document.querySelector(".dt-search");
    const resultsBox = document.querySelector(".dt-search-results");

    input.addEventListener("focus", () => {
      renderRecents(); // 🔥 show history on focus
      resultsBox?.classList.add("show");
    });

    input.addEventListener("blur", () => {
      setTimeout(() => {
        if (!searchBox.matches(":hover") && screenSize > 768) { // keep open on desktop if hovering results
          resultsBox?.classList.remove("show");
          searchBox?.classList.remove("open");
        }
      }, 150);
    });

    input.addEventListener("input", (e) => {
      const query = e.target.value.trim();

      clearTimeout(debounceTimer);

      if (!query) {
        renderRecents();
        return;
      }

      if (query.length < 3) return;

      debounceTimer = setTimeout(() => {
        runSearch(query);
      }, 300);
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const q = input.value.trim();
        if (q) {
          saveRecent(q);
          window.location.href = `product/search?q=${encodeURIComponent(q)}`;
        }
      }
    });

    function runSearch(query) {
      frappe.call({
        method: "webshop.templates.pages.product_search.search",
        args: { query },
        callback: (res) => {
          const data = res.message || {};
          renderResults(data.product_results, data.category_results);

          if (data.product_results?.length || data.category_results?.length) {
            saveRecent(query);
          }
        }
      });
    }

    function renderResults(products = [], categories = []) {
      const container = document.querySelector(".dt-search-results");

      let html = "";
      html += `
            <div class="close_search_results">
                <svg class="icon icon-sm">
                  <use href="#icon-x"></use>
                </svg>
            </div>`

      // Categories
      if (categories.length) {
        html += `
          <div class="dt-search-section">
            <div class="dt-search-title">Categories</div>
            ${categories.map(c => `
              <a href="/${c.route}" class="dt-search-chip">
                ${c.name}
              </a>
            `).join(",")}
          </div>
        `;
      }

      // Products
      if (products.length) {
        html += `
          <div class="dt-search-section">
            <div class="dt-search-title">Products</div>
            ${products.map(p => `
              <a href="/${p.route}" data-item-code="${p.item_code}">
                <div class="dt-search-item">
                  <img src="${p.thumbnail || '/assets/webshop/images/cart-empty-state.png'}" />
                  <p>${p.web_item_name}</p>
                </div>
              </a>
            `).join("")}
          </div>
        `;
      }

      if (!html) {
        html = `<div class="dt-empty">No results</div>`;
      }

      container.innerHTML = html;

      document.querySelector(".close_search_results")?.addEventListener("click", () => {
        const resultsBox = document.querySelector(".dt-search-results");
        const searchBox = document.querySelector(".dt-navbar-center");

        resultsBox?.classList.remove("show");
        searchBox?.classList.remove("open");
      });

      // 🔥 TRACK SEARCH CLICKS
      container.querySelectorAll('.dt-search-item').forEach(itemEl => {
        const link = itemEl.closest('a');

        if (!link) return;

        link.addEventListener('click', (e) => {
          const href = link.getAttribute('href');

          // extract route → item_code (adjust if needed)
          const item_code = link.dataset.itemCode;

          const query = document.querySelector(".dt-search")?.value || null;

          // fire and forget (don’t block navigation)
          fetch('/api/method/dt_recomendations.api.log_search_click', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({ item_code, query }),
            keepalive: true
          });
        });
      });

    }

    const MAX_RECENTS = 4;

    function getRecents() {
      return JSON.parse(localStorage.getItem("recent_searches") || "[]");
    }

    function saveRecent(query) {
      let recents = getRecents();

      // remove duplicate
      recents = recents.filter(q => q !== query);

      // add latest
      recents.push(query);

      // limit
      if (recents.length > MAX_RECENTS) {
        recents.shift();
      }

      localStorage.setItem("recent_searches", JSON.stringify(recents));
    }
    function renderRecents() {
      const recents = getRecents();
      const container = document.querySelector(".dt-search-results");

      if (!recents.length) {
        container.innerHTML = `<div class="dt-empty">No searches yet</div>`;
        return;
      }

      container.innerHTML = `
        <div class="dt-search-section">
          <div class="close_search_results">
              <svg class="icon icon-sm">
                <use href="#icon-x"></use>
              </svg>
          </div>
          <div class="dt-search-title">Recent</div>
          ${recents.map(q => `
            <div class="dt-search-item dt-recent" data-query="${q}">
              🕘 ${q}
            </div>
          `).join("")}
        </div>
      `;

      // click on recent
      container.querySelectorAll(".dt-recent").forEach(el => {
        el.addEventListener("click", () => {
          const q = el.dataset.query;
          document.querySelector(".dt-search").value = q;
          runSearch(q);
        });
      });

      document.querySelector(".close_search_results")?.addEventListener("click", () => {
        const resultsBox = document.querySelector(".dt-search-results");
        const searchBox = document.querySelector(".dt-navbar-center");

        resultsBox?.classList.remove("show");
        searchBox?.classList.remove("open");
      });

    }

    const wrapper = document.querySelector(".dt-search-wrapper");
    const clearBtn = document.querySelector(".dt-search-clear");

    // toggle clear button visibility
    input.addEventListener("input", () => {
      if (input.value.trim().length > 0) {
        wrapper.classList.add("has-value");
      } else {
        wrapper.classList.remove("has-value");
      }
    });

    // clear input
    clearBtn.addEventListener("click", (e) => {
      e.stopPropagation();

      input.value = "";
      wrapper.classList.remove("has-value");

      input.focus();

      renderRecents(); // optional: show recents again
    });

  }

  // LOGOUT
  document.querySelector('[data-action="logout"]')?.addEventListener("click", (e) => {
    e.preventDefault();
    frappe.call({ method: "logout", callback: () => { window.location.href = "/login"; } });
  });

  // OUTSIDE CLICK (safe version)
  document.addEventListener("click", (e) => {
    if (dropdown && !dropdown.contains(e.target)) {
      dropdown.classList.remove("open");
    }
    const resultsBox = document.querySelector(".dt-search-results");

    if (
      searchBox &&
      !searchBox.contains(e.target) &&
      !searchTrigger?.contains(e.target)
    ) {
      if(!e.target.classList.contains("dt-recent")){
        searchBox?.classList.remove("open");
        resultsBox?.classList.remove("show");
      }
    }
  });
});

frappe.ready(() => {
  if (window.webshop && webshop.webshop && webshop.webshop.wishlist) {
    webshop.webshop.wishlist.set_wishlist_count();
  }
});