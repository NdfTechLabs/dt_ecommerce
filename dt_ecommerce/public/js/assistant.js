frappe.ready(() => {
	if (!window.DT_ASSISTANT) {
		return;
	}

	const config = window.DT_ASSISTANT;

 config.ui={
  active_capability:"",
  view:""
 }

	if (!config.enabled) {
		return;
	}

	// Respect device visibility settings
	const isMobile = window.matchMedia("(max-width: 767px)").matches;

	if (isMobile && !config.show_on_mobile) {
		return;
	}

	if (!isMobile && !config.show_on_desktop) {
		return;
	}

	createAssistantButton(config);
});


function createAssistantButton(config) {
	// Prevent duplicate initialization
	if (document.getElementById("dt-assistant-button")) {
		return;
	}

	const button = document.createElement("button");

	button.id = "dt-assistant-button";
	button.type = "button";
	button.className = "dt-assistant-button";

	// Icon
	const icon = document.createElement("span");
	icon.className = "dt-assistant-button-icon";

	if (config.assistant_icon) {
		const image = document.createElement("img");

		image.src = config.assistant_icon;
		image.alt = config.assistant_name || "Assistant";

		icon.appendChild(image);
	} else {
		icon.innerHTML = `
			<svg
				viewBox="0 0 24 24"
				width="20"
				height="20"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"
			>
				<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8
					8.5 8.5 0 0 1-7.6 4.7
					8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7
					A8.38 8.38 0 0 1 4 11.5
					8.5 8.5 0 0 1 8.7 3.9
					8.38 8.38 0 0 1 12.5 3
					h.5a8.5 8.5 0 0 1 8 8.5z"
				/>
			</svg>
		`;
	}

	// Label
	const label = document.createElement("span");
	label.className = "dt-assistant-button-label";
	label.textContent = config.button_label || "Help?";

	button.appendChild(icon);
	button.appendChild(label);

	// Position
	if (config.position === "Bottom Left") {
		button.classList.add("dt-assistant-bottom-left");
	} else {
		button.classList.add("dt-assistant-bottom-right");
	}

	button.addEventListener("click", () => {
		openAssistant(config);
	});

	document.body.appendChild(button);
}


function openAssistant(config) {
 
	let panel = document.getElementById("dt-assistant-panel");

	if (!panel) {
		panel = createAssistantPanel(config);
		document.body.appendChild(panel);
	}

	panel.classList.add("dt-assistant-panel-open");
 if (config.position === "Bottom Left") {
  panel.classList.add("dt-assistant-panel-left");
 } else {
  panel.classList.add("dt-assistant-panel-right");
 }

	// Prevent page scrolling while the panel is open on mobile
	if (window.matchMedia("(max-width: 767px)").matches) {
		document.body.classList.add("dt-assistant-open");
	}
}


function closeAssistant() {
	const panel = document.getElementById("dt-assistant-panel");

	if (!panel) {
		return;
	}

	panel.classList.remove("dt-assistant-panel-open");
	document.body.classList.remove("dt-assistant-open");
}


function createAssistantPanel(config) {
	const panel = document.createElement("section");

	panel.id = "dt-assistant-panel";
	panel.className = "dt-assistant-panel";

	/*
	 * Header
	 */
	const header = document.createElement("div");
	header.className = "dt-assistant-panel-header";

	const headerContent = document.createElement("div");
	headerContent.className = "dt-assistant-panel-header-content";

	const title = document.createElement("div");
	title.className = "dt-assistant-panel-title";
	title.textContent = config.panel_title || config.assistant_name || "Assistant";

	const subtitle = document.createElement("div");
	subtitle.className = "dt-assistant-panel-subtitle";
	subtitle.textContent = config.assistant_name || "Assistant";

	headerContent.appendChild(title);
	headerContent.appendChild(subtitle);

	const closeButton = document.createElement("button");

	closeButton.type = "button";
	closeButton.className = "dt-assistant-panel-close";
	closeButton.setAttribute("aria-label", "Close assistant");

	closeButton.innerHTML = `
		<svg
			viewBox="0 0 24 24"
			width="20"
			height="20"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
		>
			<path d="M18 6L6 18"></path>
			<path d="M6 6L18 18"></path>
		</svg>
	`;

	closeButton.addEventListener("click", closeAssistant);

	header.appendChild(headerContent);
	header.appendChild(closeButton);


	/*
	 * Body
	 */
	const body = document.createElement("div");
	body.className = "dt-assistant-panel-body";

	/*
	 * Greeting
	 */
	if (config.greeting) {
		const greeting = document.createElement("div");

		greeting.className = "dt-assistant-greeting";
		greeting.textContent = config.greeting;

		body.appendChild(greeting);
	}


	/*
	 * Capabilities
	 */
	const capabilities = [...(config.capabilities || [])]
		.sort((a, b) => (a.display_order || 0) - (b.display_order || 0));

	if (capabilities.length) {
		const capabilitySection = document.createElement("div");

		capabilitySection.className = "dt-assistant-section";

		const capabilityTitle = document.createElement("div");

		capabilityTitle.className = "dt-assistant-section-title";
		capabilityTitle.textContent = "How can we help?";

		const capabilityList = document.createElement("div");

		capabilityList.className = "dt-assistant-capabilities";

		capabilities.forEach((capability) => {
			const item = createCapabilityItem(capability,config);

			capabilityList.appendChild(item);
		});

		capabilitySection.appendChild(capabilityTitle);
		capabilitySection.appendChild(capabilityList);

		body.appendChild(capabilitySection);
	}


	/*
	 * Channels
	 */
	const channels = [...(config.channels || [])]
		.sort((a, b) => (a.display_order || 0) - (b.display_order || 0));

	if (channels.length) {
		const channelSection = document.createElement("div");

		channelSection.className = "dt-assistant-section";

		const channelTitle = document.createElement("div");

		channelTitle.className = "dt-assistant-section-title";
		channelTitle.textContent = "Contact us";

		const channelList = document.createElement("div");

		channelList.className = "dt-assistant-channels";

		channels.forEach((channel) => {
			const item = createChannelItem(channel);

			if (item) {
				channelList.appendChild(item);
			}
		});

		if (channelList.children.length) {
			channelSection.appendChild(channelTitle);
			channelSection.appendChild(channelList);

			body.appendChild(channelSection);
		}
	}


	/*
	 * Assemble panel
	 */
	panel.appendChild(header);
	panel.appendChild(body);

	return panel;
}


function createCapabilityItem(capability,config) {
	const button = document.createElement("button");

	button.type = "button";
	button.className = "dt-assistant-capability";

	if (capability.icon) {
		const icon = document.createElement("span");

		icon.className = "dt-assistant-item-icon";
		icon.innerHTML = capability.icon;

		button.appendChild(icon);
	}

	const content = document.createElement("span");

	content.className = "dt-assistant-item-content";

	const label = document.createElement("span");

	label.className = "dt-assistant-item-label";
	label.textContent = formatAssistantLabel(capability.key);

	content.appendChild(label);

	if (capability.description) {
		const description = document.createElement("span");

		description.className = "dt-assistant-item-description";
		description.textContent = capability.description;

		content.appendChild(description);
	}

	const arrow = document.createElement("span");

	arrow.className = "dt-assistant-item-arrow";
	arrow.innerHTML = "›";

	button.appendChild(content);
	button.appendChild(arrow);

	button.addEventListener("click", () => {
		handleCapability(capability,config);
	});

	return button;
}


function createChannelItem(channel) {
	const button = document.createElement("button");

	button.type = "button";
	button.className = "dt-assistant-channel";

	if (channel.icon) {
		const icon = document.createElement("span");

		icon.className = "dt-assistant-item-icon";
		icon.innerHTML = channel.icon;

		button.appendChild(icon);
	}

	const content = document.createElement("span");

	content.className = "dt-assistant-item-content";

	const label = document.createElement("span");

	label.className = "dt-assistant-item-label";
	label.textContent = channel.label || formatAssistantLabel(channel.key);

	content.appendChild(label);

	if (channel.description) {
		const description = document.createElement("span");

		description.className = "dt-assistant-item-description";
		description.textContent = channel.description;

		content.appendChild(description);
	}

	button.appendChild(content);

	button.addEventListener("click", () => {
		handleChannel(channel);
	});

	return button;
}

function handleCapability(capability,config) {
 
	if (!capability || !capability.key) {
		return;
	}

	switch (capability.key) {
		case "Product Help":
			openProductHelp(capability,config);
			break;

		case "Order Help":
			openOrderTracking(capability);
			break;

		case "Delivery Help":
			openDeliveryHelp(capability);
			break;

		default:
			console.warn(
				"Unsupported assistant capability:",
				capability.key
			);
	}
}

function renderAssistantHome() {
	const config = window.DT_ASSISTANT;

	if (!config) {
		return;
	}

	const panel = document.getElementById("dt-assistant-panel");

	if (!panel) {
		return;
	}

	const body = panel.querySelector(".dt-assistant-panel-body");

	if (!body) {
		return;
	}

	// Reset assistant UI state
	if (config.ui) {
		config.ui.active_capability = "";
		config.ui.view = "";
	}

	body.innerHTML = "";

	/*
	 * Greeting
	 */

	if (config.greeting) {
		const greeting = document.createElement("div");

		greeting.className = "dt-assistant-greeting";
		greeting.textContent = config.greeting;

		body.appendChild(greeting);
	}

	/*
	 * Capabilities
	 */

	const capabilities = [...(config.capabilities || [])]
		.sort(
			(a, b) =>
				(a.display_order || 0) -
				(b.display_order || 0)
		);

	if (capabilities.length) {
		const capabilitySection =
			document.createElement("div");

		capabilitySection.className =
			"dt-assistant-section";

		const capabilityTitle =
			document.createElement("div");

		capabilityTitle.className =
			"dt-assistant-section-title";

		capabilityTitle.textContent =
			"How can we help?";

		const capabilityList =
			document.createElement("div");

		capabilityList.className =
			"dt-assistant-capabilities";

		capabilities.forEach((capability) => {
			const item = createCapabilityItem(
				capability,
				config
			);

			capabilityList.appendChild(item);
		});

		capabilitySection.appendChild(
			capabilityTitle
		);

		capabilitySection.appendChild(
			capabilityList
		);

		body.appendChild(capabilitySection);
	}

	/*
	 * Channels
	 */

	const channels = [...(config.channels || [])]
		.sort(
			(a, b) =>
				(a.display_order || 0) -
				(b.display_order || 0)
		);

	if (channels.length) {
		const channelSection =
			document.createElement("div");

		channelSection.className =
			"dt-assistant-section";

		const channelTitle =
			document.createElement("div");

		channelTitle.className =
			"dt-assistant-section-title";

		channelTitle.textContent =
			"Contact us";

		const channelList =
			document.createElement("div");

		channelList.className =
			"dt-assistant-channels";

		channels.forEach((channel) => {
			const item = createChannelItem(channel);

			if (item) {
				channelList.appendChild(item);
			}
		});

		if (channelList.children.length) {
			channelSection.appendChild(
				channelTitle
			);

			channelSection.appendChild(
				channelList
			);

			body.appendChild(
				channelSection
			);
		}
	}
}

function openProductHelp(capability,config) {
	console.log("Product Help", capability);

	config.ui.active_capability = "product_help";
	config.ui.view = "product_help";

	renderProductHelp();
}

function closeProductHelp() {
	const config = window.DT_ASSISTANT;

	if (!config) {
		return;
	}

	// Reset Product Help state
	if (config.ui) {
		config.ui.active_capability = "";
		config.ui.view = "";
	}

	// Return to the main assistant view
	renderAssistantHome();
}


function renderProductHelp() {
	const panel = document.getElementById("dt-assistant-panel");

	if (!panel) {
		return;
	}

	const body = panel.querySelector(".dt-assistant-panel-body");

	if (!body) {
		return;
	}

	body.innerHTML = `
		<div class="dt-assistant-view dt-assistant-product-help">

			<div class="dt-assistant-view-header">
				<button
					type="button"
					class="dt-assistant-back"
					aria-label="Back"
				>
					←
				</button>

				<div>
					<div class="dt-assistant-view-title">
						Product Help
					</div>

					<div class="dt-assistant-view-subtitle">
						What are you looking for?
					</div>
				</div>
			</div>

			<div class="dt-assistant-product-search">
				<span class="dt-assistant-product-search-icon">
					<svg
						viewBox="0 0 24 24"
						width="18"
						height="18"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<circle cx="11" cy="11" r="7"></circle>
						<path d="m20 20-4-4"></path>
					</svg>
				</span>

				<input
					type="search"
					class="dt-assistant-product-search-input"
					placeholder="Search products..."
					autocomplete="off"
				>
			</div>

			<div class="dt-assistant-product-results"></div>

			<div class="dt-assistant-popular">
				<div class="dt-assistant-section-title">
					Popular categories
				</div>

				<div class="dt-assistant-category-grid">

					<button
						type="button"
						class="dt-assistant-category"
						data-item-group="Wine"
					>
						Wine
					</button>

					<button
						type="button"
						class="dt-assistant-category"
						data-item-group="Whisky"
					>
						Whisky
					</button>

					<button
						type="button"
						class="dt-assistant-category"
						data-item-group="Vodka"
					>
						Vodka
					</button>

					<button
						type="button"
						class="dt-assistant-category"
						data-item-group="Gin"
					>
						Gin
					</button>

					<button
						type="button"
						class="dt-assistant-category"
						data-item-group="Cognac"
					>
						Cognac
					</button>

					<button
						type="button"
						class="dt-assistant-category"
						data-item-group="Tequila"
					>
						Tequila
					</button>

				</div>
			</div>

			<button
				type="button"
				class="dt-assistant-browse-all"
			>
				Browse all products
			</button>

		</div>
	`;
  let button = document.querySelector(".dt-assistant-back")
 	button.addEventListener("click", () => {
   renderAssistantHome();
  });
  let searchInput = document.querySelector(".dt-assistant-product-search-input")
  searchInput.addEventListener("keyup",(evt)=>{
   if(evt.target.value!==""){
    searchAssistantProducts(evt.target.value,body)
   }else{
			  body.querySelector(
      ".dt-assistant-product-results"
     ).innerHTML="";
   }
  })


	// bindProductHelpEvents(body);
}


function searchAssistantProducts(
	query,
	container,
	options = {}
) {
	const results = container.querySelector(
		".dt-assistant-product-results"
	);

	if (!results) {
		return;
	}

	results.innerHTML = `
		<div class="dt-assistant-loading">
			Searching...
		</div>
	`;

	frappe.call({
		method: "webshop.templates.pages.product_search.search",

		args: {
			query: query,
		},

		callback: (res) => {
			const data = res.message || {};

			renderProductHelpResults(
				data.product_results || [],
				data.category_results || [],
				results
			);
		},
	});
}

function renderProductHelpResults(
	products = [],
	categories = [],
	container
) {
	if (!container) {
		return;
	}

	let html = "";

	/*
	 * Categories
	 */

	if (categories.length) {
		html += `
			<div class="dt-assistant-results-section">

				<div class="dt-assistant-section-title">
					Categories
				</div>

				<div class="dt-assistant-category-results">

					${categories.map((category) => `
						<a
							href="/${category.route}"
							class="dt-assistant-result-category"
						>
							<span>
								${category.name}
							</span>

							<span class="dt-assistant-result-arrow">
								›
							</span>
						</a>
					`).join("")}

				</div>

			</div>
		`;
	}

	/*
	 * Products
	 */

	if (products.length) {
		html += `
			<div class="dt-assistant-results-section">

				<div class="dt-assistant-section-title">
					Products
				</div>

				<div class="dt-assistant-product-list">

					${products.map((product) => `
						<a
							href="/${product.route}"
							class="dt-assistant-product-result"
							data-item-code="${product.item_code}"
						>

							<div class="dt-assistant-product-result-image">
								<img
									src="${
										product.thumbnail ||
										product.website_image ||
										"/assets/webshop/images/cart-empty-state.png"
									}"
									alt="${product.web_item_name || ""}"
								>
							</div>

							<div class="dt-assistant-product-result-content">

								<div class="dt-assistant-product-result-name">
									${product.web_item_name || product.item_code}
								</div>

								${product.item_group ? `
									<div class="dt-assistant-product-result-group">
										${product.item_group}
									</div>
								` : ""}

							</div>

							<div class="dt-assistant-result-arrow">
								›
							</div>

						</a>
					`).join("")}

				</div>

			</div>
		`;
	}

	/*
	 * No results
	 */

	if (!products.length && !categories.length) {
		html = `
			<div class="dt-assistant-no-results">
				<div class="dt-assistant-no-results-title">
					No products found
				</div>

				<div class="dt-assistant-no-results-text">
					Try a different product name or search term.
				</div>
			</div>
		`;
	}

	container.innerHTML = html;
}


function openOrderTracking(capability) {
	console.log("Order Tracking", capability);

	/*
	 * Order Tracking machine will go here.
	 */
}


function openDeliveryHelp(capability) {
	console.log("Delivery Help", capability);

	/*
	 * Delivery Help machine will go here.
	 */
}



function handleChannel(channel) {
	console.log("Assistant channel selected:", channel);

	/*
	 * Channel handlers will be connected here.
	 *
	 * Example:
	 *
	 * whatsapp
	 * web_chat
	 */
}


function formatAssistantLabel(key) {
	if (!key) {
		return "";
	}

	return key
		.replace(/[_-]+/g, " ")
		.replace(/\b\w/g, (char) => char.toUpperCase());
}