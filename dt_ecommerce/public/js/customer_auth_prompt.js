/* =========================================================
   Customer Authentication Prompt
   ========================================================= */

function showCustomerAuthPrompt(options = {}) {
    const {
        title = "Sign in to continue",
        message = "You need to sign in or create an account to continue.",
        onContinue = null,
    } = options;

    let dialog = document.getElementById(
        "customer-auth-prompt-dialog"
    );

    if (!dialog) {
        dialog = document.createElement("div");

        dialog.id = "customer-auth-prompt-dialog";
        dialog.className = "customer-dialog";

        dialog.innerHTML = `
            <div class="customer-dialog-backdrop"></div>

            <div class="customer-dialog-panel customer-auth-prompt-panel">

                <div class="customer-dialog-header">

                    <div>
                        <span class="customer-dialog-eyebrow">
                            CUSTOMER ACCOUNT
                        </span>

                        <h2 data-auth-prompt-title>
                            ${frappe.utils.escape_html(title)}
                        </h2>
                    </div>

                    <button
                        type="button"
                        class="customer-dialog-close"
                        data-auth-prompt-close
                        aria-label="Close"
                    >
                        ×
                    </button>

                </div>

                <div class="customer-auth-prompt-content">

                    <div class="customer-auth-prompt-icon">
                        <svg class="icon icon-md">
                            <use href="#icon-user"></use>
                        </svg>
                    </div>

                    <h3>
                        ${frappe.utils.escape_html(title)}
                    </h3>

                    <p data-auth-prompt-message>
                        ${frappe.utils.escape_html(message)}
                    </p>

                    <div class="customer-auth-prompt-actions">

                        <a
                            href="/login"
                            class="btn btn-primary"
                            data-auth-prompt-login
                        >
                            Sign in
                        </a>

                        <a
                            href="/login#signup"
                            class="btn btn-secondary"
                            data-auth-prompt-signup
                        >
                            Create account
                        </a>

                        <button
                            type="button"
                            class="customer-auth-prompt-continue"
                            data-auth-prompt-continue
                        >
                            Continue as guest
                        </button>

                    </div>

                </div>

            </div>
        `;

        document.body.appendChild(dialog);

        bindCustomerAuthPrompt(dialog);
    }

    const messageElement = dialog.querySelector(
        "[data-auth-prompt-message]"
    );

    if (messageElement) {
        messageElement.textContent = message;
    }

    dialog._onContinue = onContinue;

    dialog.hidden = false;
    document.body.classList.add("customer-dialog-open");
}


function closeCustomerAuthPrompt() {
    const dialog = document.getElementById(
        "customer-auth-prompt-dialog"
    );

    if (!dialog) {
        return;
    }

    dialog.hidden = true;

    document.body.classList.remove(
        "customer-dialog-open"
    );

    dialog._onContinue = null;
    window.location = window.location.href.split("#")[0];
}


function bindCustomerAuthPrompt(dialog) {

    const closeButton = dialog.querySelector(
        "[data-auth-prompt-close]"
    );

    const continueButton = dialog.querySelector(
        "[data-auth-prompt-continue]"
    );

    closeButton?.addEventListener(
        "click",
        closeCustomerAuthPrompt
    );

    continueButton?.addEventListener(
        "click",
        () => {

            const callback = dialog._onContinue;

            closeCustomerAuthPrompt();

            if (typeof callback === "function") {
                callback();
            }
        }
    );

    dialog
        .querySelector(".customer-dialog-backdrop")
        ?.addEventListener(
            "click",
            closeCustomerAuthPrompt
        );
}

function getCustomerAuthAction() {
    return frappe.webshop.webshop_settings?.redirect_on_action || "";
}

/* =========================================================
   Customer Authentication Prompt Hash Handler
   ========================================================= */

const CUSTOMER_AUTH_PROMPT_HASH = "#authPrompt";

function handleCustomerAuthPromptHash() {
    if (
        window.location.hash !==
        CUSTOMER_AUTH_PROMPT_HASH
    ) {
        return;
    }

    showCustomerAuthPrompt();

    /*
     * #authPrompt is only a trigger.
     * Remove it immediately so the same action
     * can trigger it again later.
     */
    window.location.hash = "authPromptHandled";
}


/*
 * Handle #authPrompt when the page loads.
 */
document.addEventListener("DOMContentLoaded", function () {
    handleCustomerAuthPromptHash();
});


/*
 * Handle #authPrompt when Webshop changes the hash
 * without doing a full page reload.
 */
window.addEventListener(
    "hashchange",
    handleCustomerAuthPromptHash
);