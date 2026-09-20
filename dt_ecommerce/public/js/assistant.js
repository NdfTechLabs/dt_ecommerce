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

function handleCapability(capability) {
	renderCapabilityHelp(capability);
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


function renderCapabilityHelp(capability) {
	const panel = document.getElementById("dt-assistant-panel");

	if (!panel) {
		return;
	}

	const body = panel.querySelector(".dt-assistant-panel-body");

	if (!body) {
		return;
	}

	const articles = capability.articles || [];
	const actions = capability.actions || [];

	body.innerHTML = `
		<div class="dt-assistant-view dt-assistant-capability-help">

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
						${escapeHtml(capability.label || capability.key)}
					</div>

					${
						capability.description
							? `
								<div class="dt-assistant-view-subtitle">
									${escapeHtml(capability.description)}
								</div>
							`
							: ""
					}
				</div>

			</div>


			${
				articles.length
					? `
						<div class="dt-assistant-help-section">

							<div class="dt-assistant-section-title">
								Help
							</div>

							<div class="dt-assistant-article-list">

								${articles
									.map(
										(article) => `
											<a
												href="/helpdesk/kb/articles/${article.article}"
												class="dt-assistant-article"
											>

												<div class="dt-assistant-article-content">

													<div class="dt-assistant-article-title">
														${escapeHtml(article.title)}
													</div>

													${
														article.description
															? `
																<div class="dt-assistant-article-description">
																	${escapeHtml(article.description)}
																</div>
															`
															: ""
													}

												</div>

												<span class="dt-assistant-result-arrow">
													›
												</span>

											</a>
										`
									)
									.join("")}

							</div>

						</div>
					`
					: ""
			}


			${
				actions.length
					? `
						<div class="dt-assistant-help-section">

							<div class="dt-assistant-section-title">
								What would you like to do?
							</div>

							<div class="dt-assistant-action-list">

								${actions
									.map(
										(action) => `
											<a
												href="${action.link}"
												class="dt-assistant-action"
											>

												${
													action.icon
														? `
															<span class="dt-assistant-action-icon">
																${action.icon}
															</span>
														`
														: ""
												}

												<div class="dt-assistant-action-content">

													<div class="dt-assistant-action-title">
														${escapeHtml(action.label)}
													</div>

													${
														action.description
															? `
																<div class="dt-assistant-action-description">
																	${escapeHtml(action.description)}
																</div>
															`
															: ""
													}

												</div>

												<span class="dt-assistant-result-arrow">
													›
												</span>

											</a>
										`
									)
									.join("")}

							</div>

						</div>
					`
					: ""
			}


			${
				capability.ai_enabled
					? `
						<div class="dt-assistant-ai-entry">

							<button
								type="button"
								class="dt-assistant-ai-button"
								data-capability="${escapeHtml(capability.key)}"
							>
								Ask ${escapeHtml(
									window.DT_ASSISTANT?.assistant_name || "Assistant"
								)}
							</button>

						</div>
					`
					: ""
			}


			${
				!articles.length &&
				!actions.length &&
				!capability.ai_enabled
					? `
						<div class="dt-assistant-no-results">

							<div class="dt-assistant-no-results-title">
								No help available
							</div>

							<div class="dt-assistant-no-results-text">
								There is currently no help available for this topic.
							</div>

						</div>
					`
					: ""
			}

		</div>
	`;

	bindCapabilityHelpEvents(body);
}


function bindCapabilityHelpEvents(container) {
	const backButton = container.querySelector(".dt-assistant-back");

	backButton?.addEventListener("click", () => {
		renderAssistantHome();
	});

	const aiButton = container.querySelector(".dt-assistant-ai-button");

	aiButton?.addEventListener("click", () => {
		const capabilityKey = aiButton.dataset.capability;

		console.log("AI assistant requested:", capabilityKey);

		// AI machine will be implemented later.
	});
}


function escapeHtml(value) {
	const div = document.createElement("div");

	div.textContent = value ?? "";

	return div.innerHTML;
}

function handleChannel(channel) {
	
	if (!channel || !channel.enabled) {
		return;
	}

	switch (channel.channel) {
		case "whatsapp":
			openWhatsApp(channel);
			break;

		case "web_chat":
			openWebChat(channel);
			break;

		default:
			console.warn(
				"Unsupported assistant channel:",
				channel.channel
			);
	}
}

function openWhatsApp(channel) {
	if (!channel.contact) {
		console.warn("WhatsApp channel has no contact configured.");
		return;
	}

	/*
	 * Configuration example:
	 *
	 * https://wa.me/{contact}
	 */

	let url = channel.configuration;

	if (!url) {
		url = "https://wa.me/{contact}";
	}

	/*
	 * Normalize the phone number.
	 *
	 * Example:
	 * 0728583967
	 *
	 * becomes:
	 * 254728583967
	 */

	let phone = String(channel.contact)
		.replace(/\D/g, "");

	if (phone.startsWith("0")) {
		phone = "254" + phone.substring(1);
	}

	url = url.replace(
		"{contact}",
		phone
	);

	window.open(
		url,
		"_blank",
		"noopener,noreferrer"
	);
}


function openWebChat(channel) {
	console.log("Web chat channel selected:", channel);

	// Web chat implementation will come later.
}

function formatAssistantLabel(key) {
	if (!key) {
		return "";
	}

	return key
		.replace(/[_-]+/g, " ")
		.replace(/\b\w/g, (char) => char.toUpperCase());
}