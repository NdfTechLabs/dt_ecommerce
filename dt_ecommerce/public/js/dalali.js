/* Dalali Wine Wholesaler — Frontend Logic
 * All DOM mutations run inside frappe.ready() to avoid racing native webshop events.
 * Rule: never rewrite cart/qty/login state managed by webshop.webshop.shopping_cart.
 */

frappe.ready(function () {
	injectPromoBar();

	if (isDalaliItemPage()) {
		initWholesalePDP();
	}

	if (isDalaliListingPage()) {
		injectHeroSection();
		injectCategoryGrid();
		convertFiltersToHorizontal();
	}

	if (isDalaliCatalogPage()) {
		initCatalogPage();
	}

	if (document.getElementById("dalali-products")) {
		initProductCards();
	}

	if (window.location.pathname === "/cart") {
		initCartErrorFormatter();
	}
});

/* ─── Page Detection ─────────────────────────────────────── */

function isDalaliItemPage() {
	return !!document.querySelector("[data-variant-item-code], .item-main");
}

function isDalaliListingPage() {
	return !!document.querySelector(".item-group-content, #product-listing");
}

/* ─── Promo Bar ──────────────────────────────────────────── */

function injectPromoBar() {
	if (document.querySelector(".dalali-promo-bar")) return;

	const bar = document.createElement("div");
	bar.className = "dalali-promo-bar";
	bar.innerHTML = `
		<div class="dalali-promo-inner">
			<span></span>
			<span class="dalali-promo-center">
				🚚 ${__("Free Delivery on Orders Above 10 Cases")} —
				<a href="/all-products">${__("Shop Now")}</a>
			</span>
			<span class="dalali-promo-right">
				<a href="/cart">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
					</svg>
					${__("Send Wholesale Quote")}
				</a>
				<span>📞 +254 706 542 222</span>
			</span>
		</div>`;

	const header = document.querySelector("header, nav.navbar, .navbar, [class*='navbar']");
	if (header) {
		header.parentNode.insertBefore(bar, header);
	} else {
		document.body.prepend(bar);
	}
}

/* ─── PDP: Wholesale Interactions ───────────────────────── */

function initWholesalePDP() {
	const itemCode = getItemCode();
	if (!itemCode) return;

	// Bootstrap data injected by utils.py via update_website_context
	const caseSize = (window.dalali_case_size && parseInt(window.dalali_case_size)) || 12;

	// Load wine meta + tiers in parallel, then build UI
	Promise.all([
		fetchWholesaleMeta(itemCode),
		fetchPricingTiers(itemCode),
	]).then(([meta, tiers]) => {
		const bottlePrice = parseBottlePrice();

		injectUnitCaseToggle(itemCode, bottlePrice, caseSize, tiers);
		injectWineMeta(meta);
		if (tiers.length) {
			injectTierTable(tiers, bottlePrice, caseSize);
		}
	});

	// Fetch recommendations independently — doesn't need price data
	initPDPRecommended(itemCode);
}

function getItemCode() {
	// Prefer server-injected value, fall back to DOM attr
	if (window.dalali_item_code) return window.dalali_item_code;
	const el = document.querySelector("[data-variant-item-code]");
	return el ? el.dataset.variantItemCode : null;
}

function parseBottlePrice() {
	// Extract numeric value from the existing webshop price element
	const priceEl = document.querySelector(".product-price .formatted-price, .product-price span");
	if (!priceEl) return 0;
	const raw = priceEl.textContent.replace(/[^\d.]/g, "");
	return parseFloat(raw) || 0;
}

function fetchWholesaleMeta(itemCode) {
	return new Promise((resolve) => {
		frappe.call({
			method: "dt_ecommerce.api.wholesale.get_item_wholesale_meta",
			args: { item_code: itemCode },
			callback: (r) => resolve(r.message || {}),
		});
	});
}

function fetchPricingTiers(itemCode) {
	return new Promise((resolve) => {
		frappe.call({
			method: "dt_ecommerce.api.wholesale.get_pricing_tiers",
			args: { item_code: itemCode },
			callback: (r) => resolve(r.message || []),
		});
	});
}

/* Unit / Case Toggle + PDP CTA Buttons */
function injectUnitCaseToggle(itemCode, bottlePrice, caseSize, tiers) {
	const cartRow = document.querySelector(".item-cart");
	if (!cartRow) return;

	// Hide the webshop's native add-to-cart row — our buttons replace it
	cartRow.style.display = "none";

	let currentQty = 1; // tracks bottle(1) vs case(N) across toggle clicks
	const casePrice = calcCasePrice(bottlePrice, caseSize, tiers);
	const currency  = getCurrencySymbol();

	const toggleWrap = document.createElement("div");
	toggleWrap.id = "dalali-wholesale-block";
	toggleWrap.innerHTML = `
		<div class="dalali-unit-toggle">
			<button class="dalali-toggle-btn active" data-mode="bottle">${__("Bottle")}</button>
			<button class="dalali-toggle-btn" data-mode="case">${__("Case of {0}", [caseSize])}</button>
		</div>
		<div class="dalali-price-block">
			<div class="dalali-price-main" id="dalali-price-display">
				${currency} ${bottlePrice > 0 ? fmtNumber(bottlePrice) : "—"}
			</div>
			<div class="dalali-price-sub" id="dalali-price-sub">${__("per bottle")}</div>
			${tiers.length ? `<button class="dalali-tier-link" id="dalali-tier-btn">
				🔖 ${__("View volume price breaks")}
			</button>` : ""}
		</div>
		<div class="dalali-pdp-cta">
			<button class="dalali-pdp-add-btn" id="dalali-add-to-cart" type="button">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
					stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
					<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
					<path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
				</svg>
				${__("Add to Cart")}
			</button>
			<button class="dalali-pdp-buy-btn" id="dalali-buy-now" type="button">
				${__("Buy Now")}
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
					stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
					<path d="M5 12h14M12 5l7 7-7 7"/>
				</svg>
			</button>
		</div>`;

	cartRow.parentNode.insertBefore(toggleWrap, cartRow);

	// Wire toggle — updates price display and currentQty closure var
	toggleWrap.querySelectorAll(".dalali-toggle-btn").forEach((btn) => {
		btn.addEventListener("click", function () {
			toggleWrap.querySelectorAll(".dalali-toggle-btn").forEach((b) => b.classList.remove("active"));
			this.classList.add("active");
			const mode = this.dataset.mode;
			if (mode === "case") {
				currentQty = caseSize;
				document.getElementById("dalali-price-display").textContent =
					`${currency} ${fmtNumber(casePrice)}`;
				document.getElementById("dalali-price-sub").textContent =
					__("per case of {0} bottles", [caseSize]);
			} else {
				currentQty = 1;
				document.getElementById("dalali-price-display").textContent =
					`${currency} ${bottlePrice > 0 ? fmtNumber(bottlePrice) : "—"}`;
				document.getElementById("dalali-price-sub").textContent = __("per bottle");
			}
			updateCartQty(currentQty);
		});
	});

	// Tier modal trigger
	const tierBtn = document.getElementById("dalali-tier-btn");
	if (tierBtn) tierBtn.addEventListener("click", () => openTierModal(tiers, bottlePrice, caseSize));

	// CTA: Add to Cart
	document.getElementById("dalali-add-to-cart").addEventListener("click", function () {
		pdpCartAction(itemCode, currentQty, false, this);
	});

	// CTA: Buy Now → add then redirect to /cart
	document.getElementById("dalali-buy-now").addEventListener("click", function () {
		pdpCartAction(itemCode, currentQty, true, this);
	});
}

/* Shared cart action used by both PDP CTA buttons */
function pdpCartAction(itemCode, qty, buyNow, btn) {
	if (frappe.session.user === "Guest") {
		if (localStorage) localStorage.setItem("last_visited", window.location.pathname);
		window.location.href = "/login?redirect-to=" + encodeURIComponent(window.location.pathname);
		return;
	}

	const origHTML = btn.innerHTML;
	btn.disabled = true;

	frappe.call({
		method: "webshop.webshop.shopping_cart.cart.update_cart",
		args: { item_code: itemCode, qty: qty },
		callback: function (r) {
			btn.disabled = false;
			if (r.exc) return;
			if (buyNow) {
				window.location.href = "/cart";
			} else {
				btn.classList.add("added");
				btn.innerHTML = `
					<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
						stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
						<polyline points="20 6 9 17 4 12"/>
					</svg>
					${__("Added!")}`;
				setTimeout(function () {
					btn.innerHTML = origHTML;
					btn.classList.remove("added");
				}, 1800);
			}
		},
		error: function () {
			btn.disabled = false;
			window.location.href =
				"/login?redirect-to=" + encodeURIComponent(window.location.pathname);
		},
	});
}

function updateCartQty(qty) {
	// Update the qty input that webshop's add-to-cart button reads
	const qtyInput = document.querySelector(".cart-qty, input[name='qty'], .qty-input");
	if (qtyInput) {
		qtyInput.value = qty;
		qtyInput.dispatchEvent(new Event("change", { bubbles: true }));
	}
}

function calcCasePrice(bottlePrice, caseSize, tiers) {
	if (!bottlePrice) return 0;
	// Find best applicable tier for caseSize qty
	const applicable = tiers.filter((t) => !t.min_qty || t.min_qty <= caseSize);
	const best = applicable[applicable.length - 1];
	if (best) {
		if (best.rate) return best.rate * caseSize;
		if (best.discount_percentage) {
			return bottlePrice * caseSize * (1 - best.discount_percentage / 100);
		}
		if (best.discount_amount) {
			return (bottlePrice - best.discount_amount) * caseSize;
		}
	}
	return bottlePrice * caseSize;
}

/* Tier Table */
function injectTierTable(tiers, bottlePrice, caseSize) {
	const anchor = document.getElementById("dalali-wholesale-block");
	if (!anchor) return;

	const currency = getCurrencySymbol();
	const rows = tiers.map((t, i) => {
		const qtyLabel = t.max_qty
			? `${t.min_qty || 1}–${t.max_qty}`
			: `${t.min_qty || 1}+`;

		let unitPrice = bottlePrice;
		if (t.rate) unitPrice = t.rate;
		else if (t.discount_percentage) unitPrice = bottlePrice * (1 - t.discount_percentage / 100);
		else if (t.discount_amount) unitPrice = bottlePrice - t.discount_amount;

		const saving = t.discount_percentage
			? `${t.discount_percentage}% ${__("off")}`
			: t.discount_amount
			? `−${currency}${fmtNumber(t.discount_amount)}`
			: "";

		const isBest = i === tiers.length - 1;
		return `<div class="dalali-tier-row ${isBest ? "best-value" : ""}">
			<span>${__("Qty")}: ${qtyLabel}</span>
			<span>${currency} ${fmtNumber(unitPrice)} / ${__("btl")}</span>
			<span class="dalali-tier-discount">${saving}${isBest ? " ⭐" : ""}</span>
		</div>`;
	}).join("");

	const tableWrap = document.createElement("div");
	tableWrap.id = "dalali-tier-inline";
	tableWrap.innerHTML = `
		<div class="dalali-tier-table" style="margin-bottom:16px;">
			<div class="dalali-tier-row header">
				<span>${__("Quantity")}</span>
				<span>${__("Unit Price")}</span>
				<span>${__("Saving")}</span>
			</div>
			${rows}
		</div>`;

	anchor.after(tableWrap);
}

function openTierModal(tiers, bottlePrice, caseSize) {
	const currency = getCurrencySymbol();
	const rows = tiers.map((t, i) => {
		const qtyLabel = t.max_qty ? `${t.min_qty || 1}–${t.max_qty}` : `${t.min_qty || 1}+`;
		let unitPrice = bottlePrice;
		if (t.rate) unitPrice = t.rate;
		else if (t.discount_percentage) unitPrice = bottlePrice * (1 - t.discount_percentage / 100);
		else if (t.discount_amount) unitPrice = bottlePrice - t.discount_amount;
		const saving = t.discount_percentage ? `${t.discount_percentage}% ${__("off")}` : t.discount_amount ? `−${currency}${fmtNumber(t.discount_amount)}` : "";
		return `<div class="dalali-tier-row ${i === tiers.length - 1 ? "best-value" : ""}">
			<span>${__("Qty")}: ${qtyLabel}</span>
			<span>${currency} ${fmtNumber(unitPrice)}</span>
			<span class="dalali-tier-discount">${saving}</span>
		</div>`;
	}).join("");

	const overlay = document.createElement("div");
	overlay.className = "dalali-modal-overlay";
	overlay.innerHTML = `
		<div class="dalali-modal" role="dialog" aria-modal="true">
			<div class="dalali-modal-header">
				<span class="dalali-modal-title">🔖 ${__("Volume Price Breaks")}</span>
				<button class="dalali-modal-close" aria-label="${__("Close")}">✕</button>
			</div>
			<div class="dalali-tier-table">
				<div class="dalali-tier-row header">
					<span>${__("Quantity")}</span>
					<span>${__("Unit Price")}</span>
					<span>${__("Saving")}</span>
				</div>
				${rows}
			</div>
			<p style="font-size:12px;color:var(--dalali-muted);margin-top:12px;">
				${__("Prices shown per bottle. Contact our sales desk for pallet-level rates.")}
			</p>
		</div>`;

	document.body.appendChild(overlay);
	overlay.querySelector(".dalali-modal-close").addEventListener("click", () => overlay.remove());
	overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
}

/* Wine Metadata */
function injectWineMeta(meta) {
	const anchor = document.querySelector(".product-description, .dalali-pdp-details");
	if (!anchor) return;

	const fields = [
		["custom_liquor_category", __("Category")],
		["custom_wine_varietal",   __("Varietal / Style")],
		["custom_origin_country",  __("Origin")],
		["custom_region",          __("Region / Distillery")],
		["custom_vintage_year",    __("Vintage / Age")],
		["custom_alcohol_content", __("ABV %")],
	];

	const filledFields = fields.filter(([key]) => meta[key]);
	if (!filledFields.length && !meta.custom_importer_name) return;

	const items = filledFields.map(([key, label]) => `
		<div class="dalali-meta-item">
			<span class="dalali-meta-label">${label}</span>
			<span class="dalali-meta-value">${meta[key]}</span>
		</div>`).join("");

	const importerRow = meta.custom_importer_name
		? `<div class="dalali-importer-badge" style="margin-top:10px;">
				🏢 <span>${__("Imported by")}: <strong>${meta.custom_importer_name}</strong></span>
			</div>`
		: "";

	const block = document.createElement("div");
	block.id = "dalali-wine-meta";
	block.innerHTML = `
		<div class="dalali-meta-grid" style="margin-bottom:20px;">${items}</div>
		${importerRow}`;

	anchor.parentNode.insertBefore(block, anchor);
}

/* ─── PDP: Recommended Items ─────────────────────────────── */

function initPDPRecommended(itemCode) {
	const section = document.getElementById("dalali-pdp-recommended");
	if (!section) return;

	frappe.call({
		method: "dt_ecommerce.api.wholesale.get_recommended_items",
		args: { item_code: itemCode, limit: 8 },
		callback: function (r) {
			const items = r.message || [];
			if (!items.length) {
				section.style.display = "none";
				return;
			}

			const cards = items.map(function (item) {
				const img = item.website_image
					? `<img src="${item.website_image}" alt="${item.web_item_name}"
						class="dalali-rec-card-img" loading="lazy" />`
					: `<div class="dalali-cat-card-img-placeholder" aria-hidden="true">🍷</div>`;

				const priceHtml = item.price > 0
					? `<div class="dalali-rec-card-price">
							${item.currency} ${fmtNumber(item.price)}
							<span class="dalali-price-unit"> / ${__("btl")}</span>
						</div>`
					: `<div class="dalali-price-na">${__("Price on request")}</div>`;

				return `
					<article class="dalali-rec-card">
						<a href="${item.url}" class="dalali-rec-card-img-wrap"
							tabindex="-1" aria-hidden="true">${img}</a>
						<div class="dalali-rec-card-body">
							<span class="dalali-rec-card-group">${item.item_group || ""}</span>
							<a href="${item.url}" class="dalali-rec-card-name">${item.web_item_name}</a>
							${priceHtml}
						</div>
						<div class="dalali-rec-card-footer">
							<a href="${item.url}" class="dalali-rec-card-cta">${__("View & Order")}</a>
						</div>
					</article>`;
			}).join("");

			section.innerHTML = `
				<div class="container">
					<div class="dalali-section-header">
						<h2 class="dalali-section-title">${__("You May Also Like")}</h2>
						<a href="/catalog" class="dalali-section-link">${__("View all")} →</a>
					</div>
					<div class="dalali-rec-grid">${cards}</div>
				</div>`;
		},
	});
}

/* ─── Listing Page ───────────────────────────────────────── */

function injectHeroSection() {
	const groupContent = document.querySelector(".item-group-content");
	if (!groupContent || document.getElementById("dalali-hero")) return;

	const title = document.querySelector(".page_content h1, [class*='page-header'], .breadcrumb-title");
	const groupName = title ? title.textContent.trim() : __("Browse Portfolio");

	const hero = document.createElement("div");
	hero.id = "dalali-hero";
	hero.className = "dalali-hero";
	hero.innerHTML = `
		<div class="dalali-hero-inner">
			<div class="dalali-hero-tabs">
				<button class="dalali-hero-tab active" data-action="buy">${__("Buy Stock Cases")}</button>
				<button class="dalali-hero-tab" data-action="quote">${__("Bulk / Event Inquiry")}</button>
			</div>
			<p class="dalali-hero-title">
				${__("Unbeatable Wholesale Pricing for Hospitality, Bars & Retail")}
			</p>
			<div class="dalali-hero-search">
				<input type="text" id="dalali-hero-input"
					placeholder="${__("Search brands, varietals, SKU, regions...")}"
					autocomplete="off" />
				<button class="btn" id="dalali-hero-search-btn">🔍 ${__("Search")}</button>
			</div>
		</div>`;

	groupContent.parentNode.insertBefore(hero, groupContent);

	// Wire hero search
	const heroInput = document.getElementById("dalali-hero-input");
	const heroBtn = document.getElementById("dalali-hero-search-btn");
	const doSearch = () => {
		const q = heroInput.value.trim();
		if (q) window.location.href = `/product/search?q=${encodeURIComponent(q)}`;
	};
	heroBtn.addEventListener("click", doSearch);
	heroInput.addEventListener("keydown", (e) => { if (e.key === "Enter") doSearch(); });

	// Hero tabs
	hero.querySelectorAll(".dalali-hero-tab").forEach((tab) => {
		tab.addEventListener("click", function () {
			hero.querySelectorAll(".dalali-hero-tab").forEach((t) => t.classList.remove("active"));
			this.classList.add("active");
			if (this.dataset.action === "quote") {
				window.location.href = "/cart";
			}
		});
	});
}

function injectCategoryGrid() {
	// Homepage renders the grid server-side (id="dalali-category-grid") — skip JS injection
	if (document.getElementById("dalali-category-grid")) return;
	// On listing pages only (product-listing present)
	if (!document.querySelector("#product-listing")) return;

	frappe.call({
		method: "dt_ecommerce.api.wholesale.get_category_grid",
		args: { limit: 8 },
		callback: (r) => {
			const groups = r.message || [];
			if (!groups.length) return;

			const cards = groups.map((g) => {
				const img = g.image_url
					? `<img src="${g.image_url}" alt="${g.name}" class="dalali-category-img" loading="lazy" />`
					: `<div class="dalali-category-img-placeholder" aria-hidden="true">🍷</div>`;
				return `<a href="${g.url}" class="dalali-category-card">
					${img}
					<span class="dalali-category-name">${g.name}</span>
				</a>`;
			}).join("");

			const section = document.createElement("section");
			section.id = "dalali-category-grid";
			section.className = "dalali-category-section";
			section.innerHTML = `
				<div class="container">
					<div class="dalali-section-header">
						<h2 class="dalali-section-title">${__("Shop by Category")}</h2>
						<a href="/catalog" class="dalali-section-link">${__("View all")} →</a>
					</div>
					<div class="dalali-category-grid">${cards}</div>
				</div>`;

			const hero = document.getElementById("dalali-hero");
			const insertTarget = hero ? hero.nextSibling : document.querySelector(".item-group-content");
			if (insertTarget) {
				insertTarget.parentNode.insertBefore(section, insertTarget);
			}
		},
	});
}

function convertFiltersToHorizontal() {
	const sidebar = document.querySelector(".filters-section");
	const productCol = document.querySelector("#product-listing");
	const parentRow = sidebar?.closest(".row");
	if (!productCol || document.getElementById("dalali-filter-bar")) return;

	// Expand grid immediately so layout shifts don't wait for the API call
	const sidebarCol = sidebar ? sidebar.closest("[class*='col-md-3']") : null;
	if (sidebarCol) sidebarCol.style.display = "none";
	productCol.classList.remove("col-md-9");
	productCol.classList.add("col-md-12");

	// Read active filters from URL
	const qp = frappe.utils.get_query_params();
	let activeField = {};
	try { activeField = JSON.parse(qp.field_filters || "{}"); } catch (e) { /**/ }

	// Fetch filter options from our own API (independent of Webshop Settings)
	frappe.call({
		method: "dt_ecommerce.api.wholesale.get_filter_options",
		callback: function (r) {
			const opts = r.message || {};
			const defs = [
				{ name: "item_group", label: __("Type"),  values: opts.item_group || [] },
				{ name: "brand",      label: __("Brand"), values: opts.brand      || [] },
			];

			// Only build the strip if at least one filter has values
			if (!defs.some(function (d) { return d.values.length; })) return;

			const bar = document.createElement("div");
			bar.id = "dalali-filter-bar";
			bar.className = "dalali-filter-strip";

			const inner = document.createElement("div");
			inner.className = "dalali-filter-strip-inner";
			bar.appendChild(inner);

			const prefix = document.createElement("span");
			prefix.className = "dalali-filter-label";
			prefix.textContent = __("Filter by:");
			inner.appendChild(prefix);

			defs.forEach(function (def) {
				if (!def.values.length) return;

				const active = activeField[def.name] || [];

				const wrap = document.createElement("div");
				wrap.className = "dalali-filter-field";

				const lbl = document.createElement("label");
				lbl.className = "dalali-filter-field-label";
				lbl.htmlFor = "apf-" + def.name;
				lbl.textContent = def.label;

				const sel = document.createElement("select");
				sel.id = "apf-" + def.name;
				sel.className = "dalali-select";
				sel.dataset.filterName = def.name;

				const blank = document.createElement("option");
				blank.value = "";
				blank.textContent = __("All") + " " + def.label + "s";
				sel.appendChild(blank);

				def.values.forEach(function (v) {
					const opt = document.createElement("option");
					opt.value = v;
					opt.textContent = v;
					if (active.includes(v)) opt.selected = true;
					sel.appendChild(opt);
				});

				sel.addEventListener("change", function () {
					const newField = {};
					inner.querySelectorAll("[data-filter-name]").forEach(function (s) {
						if (s.value) newField[s.dataset.filterName] = [s.value];
					});
					// ensure the changed select's value is captured correctly
					if (sel.value) newField[def.name] = [sel.value];
					else           delete newField[def.name];

					const parts = {};
					if (Object.keys(newField).length) parts.field_filters = JSON.stringify(newField);
					const qs = new URLSearchParams(parts).toString();
					window.location.href = "/all-products" + (qs ? "?" + qs : "");
				});

				wrap.appendChild(lbl);
				wrap.appendChild(sel);
				inner.appendChild(wrap);
			});

			// Clear All — only when a filter is active
			if (Object.keys(activeField).length) {
				const clearLink = document.createElement("a");
				clearLink.href = "/all-products";
				clearLink.className = "dalali-ap-clear";
				clearLink.textContent = __("Clear All");
				inner.appendChild(clearLink);
			}

			// Insert strip above the product row
			const anchor = parentRow || productCol;
			anchor.parentNode.insertBefore(bar, anchor);
		},
	});
}

/* ─── Homepage: Tiered Pricing Product Cards ─────────────── */

function initProductCards() {
	const cards = Array.from(document.querySelectorAll(".dalali-product-card[data-item-code]"));
	if (!cards.length) return;

	const itemCodes = cards.map((c) => c.dataset.itemCode);

	frappe.call({
		method: "dt_ecommerce.api.wholesale.get_bulk_pricing_tiers",
		args: { item_codes: JSON.stringify(itemCodes) },
		callback: (r) => {
			const tiers = r.message || {};

			cards.forEach((card) => {
				const itemCode   = card.dataset.itemCode;
				const caseSize   = parseInt(card.dataset.caseSize) || 12;
				const bottlePrice = parseFloat(card.dataset.price) || 0;
				const currency   = card.dataset.currency || "KES";
				const tier       = tiers[itemCode] || null;

				// ── Case price ──
				const casePriceEl = card.querySelector(".dalali-case-price");
				if (casePriceEl && bottlePrice > 0) {
					const caseTotal = calcCasePrice(bottlePrice, caseSize, tier ? [tier] : []);
					casePriceEl.innerHTML =
						`<span class="dalali-case-price-amount">${currency} ${fmtNumber(caseTotal)}</span>` +
						`<span class="dalali-price-unit"> / ${__("case of {0}", [caseSize])}</span>`;
				}

				// ── Tier badge ──
				const badgeEl = card.querySelector(".dalali-tier-badge");
				if (badgeEl && tier) {
					let label = "";
					if (tier.discount_percentage) {
						label = `${tier.discount_percentage}% ${__("off")} ${tier.min_qty}+ ${__("cs")}`;
					} else if (tier.discount_amount) {
						label = `−${currency} ${fmtNumber(tier.discount_amount)} ${__("from")} ${tier.min_qty}+ ${__("cs")}`;
					} else if (tier.rate) {
						label = `${__("Fixed rate from")} ${tier.min_qty}+ ${__("cs")}`;
					}
					if (label) {
						badgeEl.innerHTML = `<span class="dalali-tier-tag">🔖 ${label}</span>`;
					}
				}
			});
		},
	});
}

/* ─── Helpers ────────────────────────────────────────────── */

function getCurrencySymbol() {
	// Read from the first price element on the page
	const priceEl = document.querySelector(".product-price span, .formatted-price");
	if (priceEl) {
		const match = priceEl.textContent.match(/^([^\d\s]+)/);
		if (match) return match[1];
	}
	return "KES";
}

function fmtNumber(n) {
	return Number(n).toLocaleString("en-KE", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

/* ─── Catalog Page (/catalog) ────────────────────────────── */

function isDalaliCatalogPage() {
	return !!document.getElementById("dalali-catalog-grid") ||
	       !!document.querySelector(".dalali-catalog-layout");
}

function initCatalogPage() {
	initPriceRangeSlider();
	initBrandSearch();
	initTierInfoButtons();
	initWishlistButtons();
	initCatalogCart();
}

/* Brand typeahead — filters the checkbox list client-side */
function initBrandSearch() {
	const input = document.getElementById("dalali-brand-search");
	const list  = document.getElementById("dalali-brand-list");
	if (!input || !list) return;

	input.addEventListener("input", function () {
		const q = this.value.toLowerCase().trim();
		list.querySelectorAll(".dalali-brand-item").forEach(function (li) {
			const name = (li.dataset.brand || "").toLowerCase();
			li.hidden = q.length > 0 && !name.includes(q);
		});
	});
}

/* Dual-thumb price range slider — syncs <input type="range"> ↔ number inputs */
function initPriceRangeSlider() {
	const rangeMin = document.getElementById("dalali-range-min");
	const rangeMax = document.getElementById("dalali-range-max");
	const inputMin = document.getElementById("dalali-price-min");
	const inputMax = document.getElementById("dalali-price-max");
	const fill     = document.getElementById("dalali-range-fill");
	if (!rangeMin || !rangeMax || !fill) return;

	function updateFill() {
		const lo  = parseInt(rangeMin.min)   || 0;
		const hi  = parseInt(rangeMin.max)   || 100;
		const vLo = parseInt(rangeMin.value) || lo;
		const vHi = parseInt(rangeMax.value) || hi;
		const span = hi - lo || 1;
		fill.style.left  = ((vLo - lo) / span * 100) + "%";
		fill.style.width = ((vHi - vLo) / span * 100) + "%";
	}

	rangeMin.addEventListener("input", function () {
		const cap = Math.min(parseInt(this.value), parseInt(rangeMax.value) - 1);
		this.value = cap;
		if (inputMin) inputMin.value = cap;
		updateFill();
	});

	rangeMax.addEventListener("input", function () {
		const cap = Math.max(parseInt(this.value), parseInt(rangeMin.value) + 1);
		this.value = cap;
		if (inputMax) inputMax.value = cap;
		updateFill();
	});

	if (inputMin) {
		inputMin.addEventListener("input", function () {
			const lo  = parseInt(rangeMin.min) || 0;
			const hi  = parseInt(inputMax ? inputMax.value : rangeMax.max) || 0;
			const cap = Math.max(lo, Math.min(parseInt(this.value) || lo, hi - 1));
			this.value = cap;
			rangeMin.value = cap;
			updateFill();
		});
	}

	if (inputMax) {
		inputMax.addEventListener("input", function () {
			const hi  = parseInt(rangeMax.max) || 100;
			const lo  = parseInt(inputMin ? inputMin.value : rangeMin.min) || 0;
			const cap = Math.min(hi, Math.max(parseInt(this.value) || hi, lo + 1));
			this.value = cap;
			rangeMax.value = cap;
			updateFill();
		});
	}

	updateFill(); // initialise fill on page load
}

/* "Why is the price variable?" — fetches tiers and opens the modal */
function initTierInfoButtons() {
	document.querySelectorAll(".dalali-cat-price-why").forEach(function (btn) {
		btn.addEventListener("click", function (e) {
			e.preventDefault();
			e.stopPropagation();

			const card = btn.closest(".dalali-cat-card");
			if (!card) return;

			const itemCode    = card.dataset.itemCode;
			const bottlePrice = parseFloat(card.dataset.price)    || 0;
			const caseSize    = parseInt(card.dataset.caseSize)    || 12;

			// Optimistic: show a generic explanation if no tiers are found
			frappe.call({
				method: "dt_ecommerce.api.wholesale.get_pricing_tiers",
				args: { item_code: itemCode },
				callback: function (r) {
					const tiers = (r.message || []).filter(
						(t) => t.min_qty > 0
					);
					if (tiers.length) {
						openTierModal(tiers, bottlePrice, caseSize);
					} else {
						openTierModal(
							[{ min_qty: 1, max_qty: null,
							   discount_percentage: 0, rate: bottlePrice }],
							bottlePrice, caseSize
						);
					}
				},
			});
		});
	});
}

/* Wishlist toggle — client-side only (no API yet) */
function initWishlistButtons() {
	document.querySelectorAll(".dalali-wishlist-btn").forEach(function (btn) {
		btn.addEventListener("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			btn.classList.toggle("active");
			const icon = btn.querySelector(".dalali-wishlist-icon");
			if (icon) {
				icon.setAttribute("fill", btn.classList.contains("active") ? "currentColor" : "none");
			}
			const label = btn.classList.contains("active")
				? __("Remove from wishlist")
				: __("Save to wishlist");
			btn.setAttribute("aria-label", label);
		});
	});
}

/* Catalog cart — calls webshop update_cart for the [🛒] button */
function initCatalogCart() {
	document.querySelectorAll(".dalali-cat-btn-add").forEach(function (btn) {
		btn.addEventListener("click", function () {
			const card = btn.closest(".dalali-cat-card");
			if (!card) return;
			const itemCode = card.dataset.itemCode;

			if (frappe.session.user === "Guest") {
				if (localStorage) localStorage.setItem("last_visited", window.location.pathname + window.location.search);
				window.location.href = "/login?redirect-to=" + encodeURIComponent(window.location.pathname + window.location.search);
				return;
			}

			// Disable briefly to prevent double-click
			btn.disabled = true;

			frappe.call({
				method: "webshop.webshop.shopping_cart.cart.update_cart",
				args: { item_code: itemCode, qty: 1 },
				callback: function (r) {
					btn.disabled = false;
					if (!r.exc) {
						// Brief success state
						btn.classList.add("added");
						const icon = btn.innerHTML;
						btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>`;
						setTimeout(function () {
							btn.innerHTML = icon;
							btn.classList.remove("added");
						}, 1600);
					}
				},
				error: function () {
					btn.disabled = false;
					// Not logged in → redirect
					window.location.href =
						"/login?redirect-to=" + encodeURIComponent(window.location.pathname + window.location.search);
				},
			});
		});
	});
}

/* ─── Cart Error Formatter ───────────────────────────────── */

function initCartErrorFormatter() {
	// cart.js extends webshop.webshop.shopping_cart at script-eval time (before
	// frappe.ready), so by the time this function runs the originals already exist.
	if (typeof webshop === "undefined") return;
	var sc = webshop.webshop.shopping_cart;
	if (!sc) return;

	function parseServerMessages(raw) {
		if (!raw) return null;
		try {
			// r._server_messages is JSON array of JSON-encoded message objects
			return JSON.parse(raw).map(function (m) {
				try { return JSON.parse(m).message || m; }
				catch (e) { return m; }
			}).filter(Boolean).join("<br>");
		} catch (e) {
			return null;
		}
	}

	function showCartError(r) {
		var msg = parseServerMessages(r._server_messages) || __("Something went wrong!");
		$("#cart-error")
			.empty()
			.html('<span class="dalali-cart-error-icon">&#9888;</span> ' + msg)
			.show();
	}

	sc.place_order = function (btn) {
		sc.freeze();
		return frappe.call({
			type: "POST",
			method: "webshop.webshop.shopping_cart.cart.place_order",
			btn: btn,
			callback: function (r) {
				if (r.exc) {
					sc.unfreeze();
					showCartError(r);
				} else {
					$(btn).hide();
					window.location.href = "/orders/" + encodeURIComponent(r.message);
				}
			}
		});
	};

	sc.request_quotation = function (btn) {
		sc.freeze();
		return frappe.call({
			type: "POST",
			method: "webshop.webshop.shopping_cart.cart.request_for_quotation",
			btn: btn,
			callback: function (r) {
				if (r.exc) {
					sc.unfreeze();
					showCartError(r);
				} else {
					$(btn).hide();
					window.location.href = "/quotations/" + encodeURIComponent(r.message);
				}
			}
		});
	};
}

/* ─── Helpers ────────────────────────────────────────────── */

// frappe's built-in __ is available on website pages; fall back gracefully
if (typeof __ === "undefined") {
	window.__ = (str) => str;
}
