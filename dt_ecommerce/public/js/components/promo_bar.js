function createPromoBar() {
	const bar = document.createElement("div");

	bar.className = "dalali-promo-bar";

	bar.innerHTML = `
		<div class="dalali-promo-inner">

			<span></span>

			<span class="dalali-social-links dalali-promo-center">

				<a href="tel:+254710561818">
					<svg class="social-icon phone">
						<use href="/assets/dt_ecommerce/images/socials.svg#phone"></use>
					</svg>
				</a>

				<a href="https://www.facebook.com/profile.php?id=61563935961287"
					target="_blank"
					rel="noopener noreferrer">

					<svg class="social-icon facebook">
						<use href="/assets/dt_ecommerce/images/socials.svg#facebook"></use>
					</svg>

				</a>

				<a href="https://www.instagram.com/dalaliwholesalers/"
					target="_blank"
					rel="noopener noreferrer">

					<svg class="social-icon instagram">
						<use href="/assets/dt_ecommerce/images/socials.svg#instagram"></use>
					</svg>

				</a>

				<a href="https://wa.me/254791687707"
					target="_blank"
					rel="noopener noreferrer">

					<svg class="social-icon whatsapp">
						<use href="/assets/dt_ecommerce/images/socials.svg#whatsapp"></use>
					</svg>

				</a>

			</span>

			<span class="dalali-promo-right">

				<a href="/cart">

					<svg width="14" height="14"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2">

						<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>

					</svg>

					${__("Send Wholesale Quote")}

				</a>

			</span>

		</div>
	`;

	return bar;
}

function injectPromoBar() {

	const header = document.querySelector(
		"header, nav.navbar, .navbar, [class*='navbar']"
	);

	const bar = createPromoBar();

	if (header) {
		header.parentNode.insertBefore(bar, header);
	} else {
		document.body.prepend(bar);
	}
}