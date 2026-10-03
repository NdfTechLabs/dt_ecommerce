frappe.ready(() => {
    const setup_migration_handler = () => {
        if (!window.login || !login.login_handlers) {
            return;
        }

        const original_401 = login.login_handlers[401];

        login.login_handlers[401] = function (xhr, data) {
            const identifier = ($("#login_email").val() || "").trim();
            // First preserve Frappe's normal behaviour if there
            // is no identifier to check.
            if (!identifier) {
                return original_401(xhr, data);
            }

            frappe.call({
                method: "dt_ecommerce.api.account_migration.check_migration",
                args: {
                    identifier: identifier
                }
            }).then((r) => {
                if (r.message?.available) {
                    show_account_migration_dialog(identifier);
                } else {
                    original_401(xhr, data);
                }
            }).catch(() => {
                original_401(xhr, data);
            });
        };
    };

    if (window.login?.login_handlers) {
        setup_migration_handler();
    } else {
        $(document).one("login_rendered", setup_migration_handler);
    }

    function show_account_migration_dialog(identifier) {
        // Prevent duplicate dialogs
        $("#dt-account-migration-modal").remove();

        const modal = $(`
            <div id="dt-account-migration-modal" class="dt-migration-overlay">
                <div class="dt-migration-modal">

                    <button
                        type="button"
                        class="dt-migration-close"
                        aria-label="${__("Close")}"
                    >
                        &times;
                    </button>

                    <div class="dt-migration-icon">
                        ✓
                    </div>

                    <h3>${__("Welcome Back")}</h3>

                    <p>
                        ${__(
                            "We found an existing customer account from our previous system."
                        )}
                    </p>

                    <p>
                        ${__(
                            "Let's verify your identity and activate your new online account."
                        )}
                    </p>

                    <button
                        type="button"
                        class="btn btn-primary dt-migration-activate"
                    >
                        ${__("Activate My Account")}
                    </button>

                </div>
            </div>
        `);

        $("body").append(modal);

        modal.find(".dt-migration-close").on("click", function () {
            modal.remove();
        });

        modal.find(".dt-migration-activate").on("click", function () {
            const button = $(this);

            button.prop("disabled", true);

            frappe.call({
                method: "dt_ecommerce.api.account_migration.activate_account",
                args: {
                    identifier: identifier
                }
            }).then((r) => {
                const result = r.message;

                if (!result?.success) {
                    return;
                }

                if (result.next_step === "otp") {
                    show_otp_section(result,identifier);
                    return;
                }

                if (result.next_step === "account_update") {
                    show_account_update_section(result,identifier);
                }
            }).catch(() => {
                button.prop("disabled", false);
            });
        });

        modal.on("click", function (e) {
            if (e.target === this) {
                modal.remove();
            }
        });
    }
    function show_otp_section(result, identifier) {
        const modal = $("#dt-account-migration-modal");

        if (!modal.length) {
            return;
        }

        const channel_text =
            result.channel === "Email"
                ? __("email")
                : __("SMS");

        modal.find(".dt-migration-modal").html(`
            <button
                type="button"
                class="dt-migration-close"
                aria-label="${__("Close")}"
            >
                &times;
            </button>

            <div class="dt-migration-icon">
                ✓
            </div>

            <h3>${__("Verify Your Account")}</h3>

            <p>
                ${__(
                    "We've sent a verification code to {0}.",
                    [result.destination]
                )}
            </p>

            <div class="dt-migration-otp-form">

                <label
                    for="dt-migration-otp"
                    class="dt-migration-otp-label"
                >
                    ${__("Verification Code")}
                </label>

                <input
                    id="dt-migration-otp"
                    type="text"
                    class="dt-migration-otp-input"
                    inputmode="numeric"
                    autocomplete="one-time-code"
                    maxlength="6"
                    placeholder="000000"
                >

                <div class="dt-migration-otp-meta">
                    <span class="dt-migration-otp-expiry">
                        ${__("Code expires in {0} minutes.", [result.expires_in])}
                    </span>
                </div>

                <button
                    type="button"
                    class="btn btn-primary dt-migration-verify"
                >
                    ${__("Verify Code")}
                </button>

            </div>
        `);

        const otp_input = modal.find("#dt-migration-otp");

        modal.find(".dt-migration-close").on("click", function () {
            modal.remove();
        });

        modal.on("click", function (e) {
            if (e.target === this) {
                modal.remove();
            }
        });

        otp_input.on("input", function () {
            this.value = this.value.replace(/\D/g, "").slice(0, 6);
        });

        otp_input.on("keydown", function (e) {
            if (e.key === "Enter") {
                modal.find(".dt-migration-verify").trigger("click");
            }
        });

        modal.find(".dt-migration-verify").on("click", function () {
            verify_migration_otp(
                result.verification_id,
                otp_input.val(),
                $(this),
                identifier
            );
        });

        otp_input.trigger("focus");
    }

    function verify_migration_otp(verification_id, otp, button, identifier) {
        otp = (otp || "").trim();

        if (!otp) {
            frappe.msgprint({
                title: __("Verification Required"),
                message: __("Please enter the verification code."),
                indicator: "orange"
            });

            return;
        }

        if (!/^\d{6}$/.test(otp)) {
            frappe.msgprint({
                title: __("Invalid Code"),
                message: __("Please enter the 6-digit verification code."),
                indicator: "orange"
            });

            return;
        }

        button.prop("disabled", true);

        frappe.call({
            method: "dt_ecommerce.api.account_migration.verify_otp",
            args: {
                verification_id: verification_id,
                otp: otp
            }
        }).then((r) => {
            const result = r.message;
            console.log(result);

            if (!result?.success || !result?.verified) {
                button.prop("disabled", false);
                return;
            }

            show_account_update_section(result, identifier);

        }).catch(() => {
            button.prop("disabled", false);
        });
    }

    function show_account_update_section(result, identifier) {
        console.log(result);
        if (
            !result?.success ||
            !result?.customer
        ) {
            return;
        }

        window.location.href =
            `/customer?name=${encodeURIComponent(result.customer)}&identifier=${encodeURIComponent(identifier)}`;
    }
});
