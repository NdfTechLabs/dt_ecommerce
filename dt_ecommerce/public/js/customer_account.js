(() => {

    "use strict";




    /* =========================================================
       Onboarding token
       ========================================================= */

    if (window.customerOnboardingToken) {
        document.cookie =
            "customer_onboarding_token=" +
            encodeURIComponent(
                window.customerOnboardingToken
            ) +
            "; Max-Age=1800" +
            "; Path=/" +
            "; SameSite=Lax";
    }


    if (window.customerOnboardingCompleted) {
        console.log(
            "Clearing customer onboarding token cookie"
        );
        document.cookie =
            "customer_onboarding_token=" +
            "; Max-Age=0" +
            "; Path=/" +
            "; SameSite=Lax";
    }

    /* =========================================================
       Dashboard
       ========================================================= */

    const dashboard = document.getElementById(
        "customer-dashboard"
    );

    if (!dashboard) {
        return;
    }


    const customerName =
        dashboard.dataset.customer;


    /* =========================================================
       Shared helpers
       ========================================================= */

    function getElement(selector) {
        return document.querySelector(selector);
    }


    function getDashboardElement(selector) {
        return dashboard.querySelector(selector);
    }


    function getFormData(form) {

        const data = {};

        new FormData(form).forEach((value, key) => {
            data[key] = value;
        });

        return data;
    }


    function setDialogState(dialog, open) {
        if (!dialog) {
            return;
        }

        dialog.hidden = !open;

        dialog.setAttribute(
            "aria-hidden",
            open ? "false" : "true"
        );

        if (open) {
            document.body.classList.add(
                "customer-dialog-open"
            );
        } else {
            const openDialogs =
                document.querySelectorAll(
                    '[aria-hidden="false"].customer-dialog'
                );

            if (!openDialogs.length) {
                document.body.classList.remove(
                    "customer-dialog-open"
                );
            }
        }
    }


    function openDialog(dialog, hash) {

        if (!dialog) {
            return;
        }

        if (
            hash &&
            window.location.hash !== hash
        ) {
            history.pushState(
                null,
                "",
                hash
            );
        }

        setDialogState(dialog, true);
    }


    function closeDialog(dialog, hash) {

        if (!dialog) {
            return;
        }

        setDialogState(dialog, false);

        if (
            hash &&
            window.location.hash === hash
        ) {
            history.pushState(
                "",
                document.title,
                window.location.pathname +
                window.location.search
            );
        }
    }


    function closeAllDialogs() {

        document
            .querySelectorAll(
                '[aria-hidden="false"]'
            )
            .forEach((dialog) => {
                setDialogState(dialog, false);
            });
    }


    function showError(title, error, fallback) {

        console.error(
            title,
            error
        );

        frappe.msgprint({
            title,
            message:
                error?.message ||
                fallback,
            indicator: "red",
        });
    }


    function setButtonLoading(
        button,
        loadingText,
        defaultText,
        loading
    ) {

        if (!button) {
            return;
        }

        button.disabled = loading;

        button.textContent = loading
            ? loadingText
            : defaultText;
    }


    /* =========================================================
       Account cards
       ========================================================= */

    const actionCards =
        dashboard.querySelectorAll(
            "[data-account-action]"
        );


    actionCards.forEach((card) => {

        card.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key !== "Enter" &&
                    event.key !== " "
                ) {
                    return;
                }

                event.preventDefault();

                card.click();
            }
        );

    });


    /* =========================================================
       Profile dialog
       ========================================================= */

    const profileDialog =
        document.getElementById(
            "customer-profile-dialog"
        );

    const profileCard =
        getDashboardElement(
            '[data-account-action="profile"]'
        );


    function openProfileDialog() {

        openDialog(
            profileDialog,
            "#profile"
        );
    }


    function closeProfileDialog() {

        closeDialog(
            profileDialog,
            "#profile"
        );
    }


    if (profileCard) {

        profileCard.addEventListener(
            "click",
            (event) => {

                event.preventDefault();

                openProfileDialog();
            }
        );
    }


    if (profileDialog) {

        profileDialog
            .querySelectorAll(
                "[data-dialog-close]"
            )
            .forEach((element) => {

                element.addEventListener(
                    "click",
                    closeProfileDialog
                );

            });
    }


    /* =========================================================
       Profile form
       ========================================================= */

    const profileForm =
        document.getElementById(
            "customer-profile-form"
        );


    if (profileForm) {

        profileForm.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();

                const submitButton =
                    profileForm.querySelector(
                        'button[type="submit"]'
                    );

                const data =
                    getFormData(profileForm);


                setButtonLoading(
                    submitButton,
                    "Saving...",
                    "Save changes",
                    true
                );


                try {

                    const response =
                        await frappe.call({

                            method:
                                "dt_ecommerce.api.customer_account.update_customer_profile",

                            args: {

                                customer_name:
                                    customerName,

                                data:
                                    JSON.stringify(
                                        data
                                    ),
                            },

                        });


                    const result =
                        response.message;


                    if (
                        !result ||
                        !result.success
                    ) {
                        throw new Error(
                            "Unable to update customer information."
                        );
                    }


                    updateCustomerDashboard(
                        result.customer
                    );


                    closeProfileDialog();

                } catch (error) {

                    showError(
                        "Unable to save changes",
                        error,
                        "Something went wrong while updating your information."
                    );

                } finally {

                    setButtonLoading(
                        submitButton,
                        "Saving...",
                        "Save changes",
                        false
                    );
                }

            }
        );
    }


    function updateCustomerDashboard(customer) {

        if (!customer) {
            return;
        }


        const accountName =
            dashboard.querySelector(
                ".summary-item strong"
            );


        if (accountName) {

            accountName.textContent =
                customer.customer_name;
        }


        const welcomeName =
            dashboard.querySelector(
                ".customer-welcome h1"
            );


        if (welcomeName) {

            welcomeName.textContent =
                `Welcome back, ${customer.customer_name}`;
        }
    }


    /* =========================================================
       Customer details dialog
       ========================================================= */

    const detailsDialog =
        document.getElementById(
            "customer-details-dialog"
        );

    const detailsCard =
        getDashboardElement(
            '[data-account-action="customer-details"]'
        );


    function openCustomerDetails() {

        openDialog(
            detailsDialog,
            "#customer-details"
        );
    }


    function closeCustomerDetails() {

        closeDialog(
            detailsDialog,
            "#customer-details"
        );
    }


    if (detailsCard) {

        detailsCard.addEventListener(
            "click",
            (event) => {

                event.preventDefault();

                openCustomerDetails();
            }
        );
    }


    if (detailsDialog) {

        detailsDialog
            .querySelectorAll(
                "[data-details-close]"
            )
            .forEach((element) => {

                element.addEventListener(
                    "click",
                    closeCustomerDetails
                );

            });
    }


    /* =========================================================
       Details -> Profile
       ========================================================= */

    const editProfileButton =
        detailsDialog?.querySelector(
            '[data-account-action="profile"]'
        );


    if (editProfileButton) {

        editProfileButton.addEventListener(
            "click",
            (event) => {

                event.preventDefault();

                closeCustomerDetails();

                openProfileDialog();
            }
        );
    }


    /* =========================================================
       Customer contacts dialog
       ========================================================= */

    const contactsDialog =
        document.getElementById(
            "customer-contacts-dialog"
        );

    const contactsCard =
        getDashboardElement(
            '[data-account-action="customer-contacts"]'
        );


    function openCustomerContacts() {

        openDialog(
            contactsDialog,
            "#customer-contacts"
        );

        loadCustomerContacts();
    }


    function closeCustomerContacts() {

        closeDialog(
            contactsDialog,
            "#customer-contacts"
        );
    }


    if (contactsCard) {

        contactsCard.addEventListener(
            "click",
            (event) => {

                event.preventDefault();

                openCustomerContacts();
            }
        );
    }


    if (contactsDialog) {

        contactsDialog
            .querySelectorAll(
                "[data-contacts-close]"
            )
            .forEach((element) => {

                element.addEventListener(
                    "click",
                    closeCustomerContacts
                );

            });
    }


    /* =========================================================
       Load customer contacts
       ========================================================= */

    async function loadCustomerContacts() {

        const contactsList =
            document.getElementById(
                "customer-contacts-list"
            );


        if (!contactsList) {
            return;
        }


        contactsList.innerHTML = `
            <div class="customer-contacts-loading">
                Loading contacts...
            </div>
        `;


        try {

            const response =
                await frappe.call({

                    method:
                        "dt_ecommerce.api.customer_account.get_customer_contacts",

                    args: {
                        customer_name:
                            customerName,
                    },

                });


            const result =
                response.message;


            if (
                !result ||
                !result.success
            ) {
                throw new Error(
                    "Unable to load customer contacts."
                );
            }


            renderCustomerContacts(
                result.contacts || []
            );

        } catch (error) {

            console.error(
                "Failed to load customer contacts:",
                error
            );


            contactsList.innerHTML = `
                <div class="customer-contacts-empty">

                    <h4>
                        Unable to load contacts
                    </h4>

                    <p>
                        We couldn't retrieve the contacts
                        for this customer account.
                    </p>

                </div>
            `;
        }
    }


    /* =========================================================
       Render customer contacts
       ========================================================= */

    function getContactName(contact) {

        return (
            contact.full_name ||
            [
                contact.first_name,
                contact.middle_name,
                contact.last_name,
            ]
                .filter(Boolean)
                .join(" ") ||
            "Unnamed contact"
        );
    }


    function renderContactPrimaryAction(contact) {

        if (contact.is_primary_contact) {
            return "";
        }

        return `
            <button
                type="button"
                data-contact-action="make-primary"
                data-contact-name="${frappe.utils.escape_html(
                    contact.name
                )}"
            >
                Make primary
            </button>
        `;
    }

    function renderContactRemoveAction(contact) {

        if (contact.is_primary_contact) {
            return "";
        }

        return `
            <button
                type="button"
                data-contact-action="remove"
                data-contact-name="${frappe.utils.escape_html(
                    contact.name
                )}"
                class="customer-contact-menu-danger"
            >
                Remove contact
            </button>
        `;
    }

    function renderContactEditAction(contact) {

        return `
            <button
                type="button"
                data-contact-action="edit"
                data-contact-name="${frappe.utils.escape_html(
                    contact.name
                )}"
            >
                Edit contact
            </button>
        `;
    }
    function renderContactViewAction(contact) {

        return `
            <button
                type="button"
                data-contact-action="view"
                data-contact-name="${frappe.utils.escape_html(
                    contact.name
                )}"
            >
                View contact
            </button>
        `;
    }
    function renderContactMenu(contact) {

        return `
            <div class="customer-contact-menu">

                ${renderContactViewAction(contact)}

                ${renderContactEditAction(contact)}

                ${renderContactPrimaryAction(contact)}

                ${renderContactRemoveAction(contact)}

            </div>
        `;
    }
    function renderContactMeta(contact) {

        const email =
            contact.email_id
                ? `
                    <span>

                        <svg class="icon icon-sm">
                            <use href="#icon-mail"></use>
                        </svg>

                        ${frappe.utils.escape_html(
                            contact.email_id
                        )}

                    </span>
                `
                : "";


        const phone =
            contact.mobile_no ||
            contact.phone;


        const phoneMarkup =
            phone
                ? `
                    <span>

                        <svg class="icon icon-sm">
                            <use href="#icon-phone"></use>
                        </svg>

                        ${frappe.utils.escape_html(
                            phone
                        )}

                    </span>
                `
                : "";


        return email + phoneMarkup;
    }


    function renderCustomerContacts(
        contacts
    ) {

        const contactsList =
            document.getElementById(
                "customer-contacts-list"
            );


        if (!contactsList) {
            return;
        }


        if (!contacts.length) {

            contactsList.innerHTML = `
                <div class="customer-contacts-empty">

                    <div class="customer-contacts-empty-icon">

                        <svg class="icon icon-md">
                            <use href="#icon-users"></use>
                        </svg>

                    </div>

                    <h4>
                        No contacts yet
                    </h4>

                    <p>
                        Add a contact to keep the people associated
                        with this customer account up to date.
                    </p>

                </div>
            `;

            return;
        }


        contactsList.innerHTML =
            contacts
                .map((contact) => {

                    const name =
                        getContactName(contact);

                    const initial =
                        name
                            .charAt(0)
                            .toUpperCase();


                    const primaryBadge =
                        contact.is_primary_contact
                            ? `
                                <span
                                    class="customer-contact-primary"
                                >
                                    Primary
                                </span>
                            `
                            : "";


                    return `
                        <div
                            class="customer-contact-item"
                            data-contact="${frappe.utils.escape_html(
                                contact.name
                            )}"
                        >

                            <div
                                class="customer-contact-avatar"
                            >
                                ${frappe.utils.escape_html(
                                    initial
                                )}
                            </div>


                            <div
                                class="customer-contact-info"
                            >

                                <div
                                    class="customer-contact-name"
                                >

                                    <strong>
                                        ${frappe.utils.escape_html(
                                            name
                                        )}
                                    </strong>

                                    ${primaryBadge}

                                </div>


                                <div
                                    class="customer-contact-meta"
                                >
                                    ${renderContactMeta(
                                        contact
                                    )}
                                </div>

                            </div>


                            <div
                                class="customer-contact-actions"
                            >

                                <button
                                    type="button"
                                    class="customer-contact-menu-button"
                                    aria-label="Contact actions"
                                    data-contact-menu
                                >
                                    <span
                                        class="customer-contact-more"
                                    >
                                        •••
                                    </span>
                                </button>


                                ${renderContactMenu(contact)}

                            </div>

                        </div>
                    `;

                })
                .join("");
    }


    /* =========================================================
       Contact menu helpers
       ========================================================= */

    function closeContactMenus(
        exceptMenu = null
    ) {

        document
            .querySelectorAll(
                ".customer-contact-menu.is-open"
            )
            .forEach((menu) => {

                if (menu !== exceptMenu) {

                    menu.classList.remove(
                        "is-open"
                    );
                }

            });
    }


    function toggleContactMenu(
        menu
    ) {

        if (!menu) {
            return;
        }

        const shouldOpen =
            !menu.classList.contains(
                "is-open"
            );


        closeContactMenus();


        if (shouldOpen) {

            menu.classList.add(
                "is-open"
            );
        }
    }


    /* =========================================================
       Contact operations
       ========================================================= */

    const contactsList =
        document.getElementById(
            "customer-contacts-list"
        );


    if (contactsList) {

        contactsList.addEventListener(
            "click",
            async (event) => {

                const menuButton =
                    event.target.closest(
                        "[data-contact-menu]"
                    );


                if (menuButton) {

                    toggleContactMenu(
                        menuButton.nextElementSibling
                    );

                    return;
                }


                const actionButton =
                    event.target.closest(
                        "[data-contact-action]"
                    );


                if (!actionButton) {
                    return;
                }


                const action =
                    actionButton.dataset.contactAction;


                const contact =
                    actionButton.dataset.contactName;


                closeContactMenus();


                if (
                    action === "make-primary"
                ) {

                    await makeContactPrimary(
                        customerName,
                        contact
                    );

                    return;
                }


                if (
                    action === "remove-primary"
                ) {

                    await removeContactPrimary(
                        customerName,
                        contact
                    );

                    return;
                }


                if (
                    action === "remove"
                ) {

                    await removeCustomerContact(
                        customerName,
                        contact
                    );
                }
                if (
                    action === "edit"
                ) {

                    await openEditCustomerContactDialog(contact);
                }
                if (action === "view") {

                    await openViewCustomerContactDialog(
                        contact
                    );

                    return;
                }

            }
        );
    }


    /* =========================================================
       Add contact dialog
       ========================================================= */

    const addContactDialog =
        document.getElementById(
            "add-customer-contact-dialog"
        );


    const addContactForm =
        document.getElementById(
            "add-customer-contact-form"
        );


    const saveContactButton =
        document.getElementById(
            "save-customer-contact"
        );


    /*
     * IMPORTANT:
     *
     * The button that OPENS the dialog should have:
     *
     * data-add-customer-contact
     *
     * The button that SUBMITS the form should have:
     *
     * id="save-customer-contact"
     *
     * Do not use the submit button as the dialog opener.
     */


    const addContactButtons =
        document.querySelectorAll(
            "[data-add-customer-contact]"
        );


    addContactButtons.forEach((button) => {

        button.addEventListener(
            "click",
            (event) => {

                event.preventDefault();

                openAddCustomerContactDialog();
            }
        );

    });


    function openAddCustomerContactDialog() {

        if (!addContactDialog) {
            return;
        }


        addContactForm?.reset();

        document.getElementById(
            "customer-contact-name"
        ).value = "";

        setCustomerContactDialogMode("create");


        addContactDialog.hidden = false;


        requestAnimationFrame(() => {

            addContactDialog.classList.add(
                "is-open"
            );

        });
    }
    async function openEditCustomerContactDialog(contactName) {

        try {

            const response = await frappe.call({

                method:
                    "dt_ecommerce.api.customer_account.get_customer_contact",

                args: {
                    customer_name: customerName,
                    contact_name: contactName,
                },

            });

            const result = response.message;

            if (
                !result ||
                !result.success ||
                !result.contact
            ) {
                throw new Error(
                    "Unable to load contact."
                );
            }

            const contact = result.contact;

            document.getElementById(
                "customer-contact-name"
            ).value = contact.name || "";

            document.getElementById(
                "contact-first-name"
            ).value = contact.first_name || "";

            document.getElementById(
                "contact-middle-name"
            ).value = contact.middle_name || "";

            document.getElementById(
                "contact-last-name"
            ).value = contact.last_name || "";

            document.getElementById(
                "contact-email"
            ).value = contact.email_id || "";

            document.getElementById(
                "contact-mobile"
            ).value = contact.mobile_no || "";

            document.getElementById(
                "contact-phone"
            ).value = contact.phone || "";

            setCustomerContactDialogMode("edit");

            let dialog=document.getElementById(
                "add-customer-contact-dialog"
            )
            dialog.hidden = false;
            requestAnimationFrame(() => {

                dialog.classList.add(
                    "is-open"
                );

            });

        } catch (error) {

            showError(
                "Unable to edit contact",
                error,
                "Something went wrong while loading the contact."
            );

        }
    }
    function closeAddCustomerContactDialog() {

        if (!addContactDialog) {
            return;
        }


        addContactDialog.classList.remove(
            "is-open"
        );


        setTimeout(() => {

            addContactDialog.hidden = true;

        }, 150);
    }


    if (addContactDialog) {

        addContactDialog
            .querySelectorAll(
                "[data-close-add-contact]"
            )
            .forEach((element) => {

                element.addEventListener(
                    "click",
                    closeAddCustomerContactDialog
                );

            });
    }


    /* =========================================================
       Create customer contact
       ========================================================= */

    async function createCustomerContact() {

        if (!addContactForm) {
            return;
        }


        const data =
            getFormData(
                addContactForm
            );


        setButtonLoading(
            saveContactButton,
            "Adding...",
            "Add contact",
            true
        );


        try {

            const response =
                await frappe.call({

                    method:
                        "dt_ecommerce.api.customer_account.create_customer_contact",

                    args: {

                        customer_name:
                            customerName,

                        data:
                            JSON.stringify(
                                data
                            ),

                    },

                });


            const result =
                response.message;


            if (
                !result ||
                !result.success
            ) {

                throw new Error(
                    "Unable to create contact."
                );
            }


            closeAddCustomerContactDialog();


            await loadCustomerContacts();


            frappe.show_alert({

                message:
                    "Contact added successfully.",

                indicator:
                    "green",

            });

        } catch (error) {

            showError(
                "Unable to add contact",
                error,
                "Something went wrong while adding the contact."
            );

        } finally {

            setButtonLoading(
                saveContactButton,
                "Adding...",
                "Add contact",
                false
            );
        }
    }

    /* =========================================================
       Contact operations
       ========================================================= */

    async function makeContactPrimary(
        customerName,
        contactName
    ) {

        try {

            const response = await frappe.call({

                method:
                    "dt_ecommerce.api.customer_account.make_customer_contact_primary",

                args: {
                    customer_name: customerName,
                    contact_name: contactName,
                },

            });


            const result = response.message;


            if (
                !result ||
                !result.success
            ) {
                throw new Error(
                    "Unable to make contact primary."
                );
            }


            await loadCustomerContacts();


            frappe.show_alert({
                message:
                    "Primary contact updated.",
                indicator:
                    "green",
            });


        } catch (error) {

            showError(
                "Unable to update primary contact",
                error,
                "Something went wrong while changing the primary contact."
            );

        }
    }


    async function removeContactPrimary(
        customerName,
        contactName
    ) {

        /*
         * This operation is no longer allowed.
         *
         * A customer must always have a primary contact.
         * The user must select another contact as primary instead.
         */

        frappe.show_alert({
            message:
                "A primary contact cannot be removed. Select another contact to make primary instead.",
            indicator:
                "orange",
        });
    }


    async function removeCustomerContact(
        customerName,
        contactName
    ) {

        try {

            const response = await frappe.call({

                method:
                    "dt_ecommerce.api.customer_account.remove_customer_contact",

                args: {
                    customer_name: customerName,
                    contact_name: contactName,
                },

            });


            const result = response.message;


            if (
                !result ||
                !result.success
            ) {
                throw new Error(
                    "Unable to remove contact."
                );
            }


            await loadCustomerContacts();


            frappe.show_alert({
                message:
                    "Contact removed.",
                indicator:
                    "green",
            });


        } catch (error) {

            showError(
                "Unable to remove contact",
                error,
                "Something went wrong while removing the contact."
            );

        }
    }

    async function updateCustomerContact() {

        const form =
            document.getElementById(
                "add-customer-contact-form"
            );

        const contactName =
            document.getElementById(
                "customer-contact-name"
            ).value;


        if (!contactName) {

            frappe.show_alert({
                message: "Contact name is missing.",
                indicator: "red",
            });

            return;
        }


        const data = Object.fromEntries(
            new FormData(form).entries()
        );


        delete data.contact_name;


        try {

            const response = await frappe.call({

                method:
                    "dt_ecommerce.api.customer_account.update_customer_contact",

                args: {
                    customer_name: customerName,
                    contact_name: contactName,
                    data: JSON.stringify(data),
                },

            });


            const result = response.message;


            if (
                !result ||
                !result.success
            ) {
                throw new Error(
                    "Unable to update contact."
                );
            }


            closeAddCustomerContactDialog();


            await loadCustomerContacts();


            frappe.show_alert({
                message: "Contact updated.",
                indicator: "green",
            });


        } catch (error) {

            showError(
                "Unable to update contact",
                error,
                "Something went wrong while updating the contact."
            );

        }
    }
    async function openViewCustomerContactDialog(contactName) {

        try {

            const response = await frappe.call({

                method:
                    "dt_ecommerce.api.customer_account.get_customer_contact",

                args: {
                    customer_name: customerName,
                    contact_name: contactName,
                },

            });

            const result = response.message;

            if (
                !result ||
                !result.success ||
                !result.contact
            ) {
                throw new Error(
                    "Unable to load contact."
                );
            }

            const contact = result.contact;


            document.getElementById(
                "customer-contact-name"
            ).value = contact.name || "";

            document.getElementById(
                "contact-first-name"
            ).value = contact.first_name || "";

            document.getElementById(
                "contact-middle-name"
            ).value = contact.middle_name || "";

            document.getElementById(
                "contact-last-name"
            ).value = contact.last_name || "";

            document.getElementById(
                "contact-email"
            ).value = contact.email_id || "";

            document.getElementById(
                "contact-mobile"
            ).value = contact.mobile_no || "";

            document.getElementById(
                "contact-phone"
            ).value = contact.phone || "";


            setCustomerContactDialogMode("view");


            let dialog = document.getElementById(
                "add-customer-contact-dialog"
            )
            dialog.hidden = false;
            requestAnimationFrame(() => {

                dialog.classList.add(
                    "is-open"
                );

            });

        } catch (error) {

            showError(
                "Unable to view contact",
                error,
                "Something went wrong while loading the contact."
            );

        }
    }

    let customerContactDialogMode = "create";

    function setCustomerContactDialogMode(mode) {

        customerContactDialogMode = mode;

        const title =
            document.getElementById(
                "customer-contact-dialog-title"
            );

        const formTitle =
            document.getElementById(
                "customer-contact-form-title"
            );

        const description =
            document.getElementById(
                "customer-contact-form-description"
            );

        const saveButton =
            document.getElementById(
                "save-customer-contact"
            );

        const form =
            document.getElementById(
                "add-customer-contact-form"
            );


        const isView =
            mode === "view";

        const isEdit =
            mode === "edit";


        if (mode === "view") {

            title.textContent =
                "Contact details";

            formTitle.textContent =
                "Contact information";

            description.textContent =
                "View the information associated with this contact.";

            saveButton.hidden = true;

        } else if (isEdit) {

            title.textContent =
                "Edit contact";

            formTitle.textContent =
                "Update contact information";

            description.textContent =
                "Update the information for this contact.";

            saveButton.hidden = false;

            saveButton.textContent =
                "Save changes";

        } else {

            title.textContent =
                "Add contact";

            formTitle.textContent =
                "Contact information";

            description.textContent =
                "Add a person associated with your customer account.";

            saveButton.hidden = false;

            saveButton.textContent =
                "Add contact";
        }


        /*
         * Enable/disable all editable form fields.
         *
         * The hidden contact_name field remains untouched.
         */
        form.querySelectorAll(
            "input:not([type='hidden'])"
        ).forEach((input) => {

            input.readOnly = isView;

            input.disabled = false;

        });
    }


    if (addContactForm) {

        addContactForm.addEventListener(
            "submit",
            async (event) => {

               event.preventDefault();


               if (customerContactDialogMode === "edit") {

                   await updateCustomerContact();

                   return;
               }


               await createCustomerContact();
            }
        );
    }


    /* =========================================================
       Dialog close buttons / Escape
       ========================================================= */

    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key !== "Escape"
            ) {
                return;
            }


            const openDialog =
                document.querySelector(
                    '[aria-hidden="false"]'
                );


            if (!openDialog) {
                return;
            }


            if (
                openDialog ===
                profileDialog
            ) {

                closeProfileDialog();

                return;
            }


            if (
                openDialog ===
                detailsDialog
            ) {

                closeCustomerDetails();

                return;
            }


            if (
                openDialog ===
                contactsDialog
            ) {

                closeCustomerContacts();

                return;
            }


            if (
                openDialog ===
                addContactDialog
            ) {

                closeAddCustomerContactDialog();
            }
        }
    );


    /* =========================================================
       Hash routing
       ========================================================= */

    function handleHashRoute() {

        const hash =
            window.location.hash;


        if (hash === "#profile") {

            closeAllDialogs();

            openProfileDialog();

            return;
        }


        if (
            hash ===
            "#customer-details"
        ) {

            closeAllDialogs();

            openCustomerDetails();

            return;
        }


        if (
            hash ===
            "#customer-contacts"
        ) {

            closeAllDialogs();

            openCustomerContacts();

            return;
        }


        /*
         * Add-contact is intentionally not part
         * of the URL hash routing.
         *
         * It is a child dialog of Contacts.
         */
    }


    window.addEventListener(
        "hashchange",
        handleHashRoute
    );


    window.addEventListener(
        "popstate",
        handleHashRoute
    );


    /* =========================================================
       Initial route
       ========================================================= */

    handleHashRoute();

    function renderDashboardOrders(orders) {

        renderDashboardList(
            "customer-dashboard-orders",
            orders,
            (order) => `
                <a
                    href="${frappe.utils.escape_html(order.url)}"
                    class="dashboard-list-item"
                >

                    <div class="dashboard-list-item-icon">
                        <svg class="icon icon-sm">
                            <use href="#icon-shopping-bag"></use>
                        </svg>
                    </div>

                    <div class="dashboard-list-item-content">

                        <strong>
                            ${frappe.utils.escape_html(order.name)}
                        </strong>

                        <span>
                            ${frappe.utils.escape_html(
                                order.transaction_date || ""
                            )}
                        </span>

                    </div>

                    <div class="dashboard-list-item-value">

                        <strong>
                            ${frappe.format(
                                order.grand_total,
                                {
                                    fieldtype: "Currency",
                                    options: order.currency,
                                }
                            )}
                        </strong>

                        <span class="dashboard-list-status">
                            ${frappe.utils.escape_html(
                                order.status || ""
                            )}
                        </span>

                    </div>

                    <svg class="icon icon-sm dashboard-list-arrow">
                        <use href="#icon-chevron-right"></use>
                    </svg>

                </a>
            `,
            "No orders found."
        );
    }
    function renderDashboardAddresses(addresses) {

        renderDashboardList(
            "customer-dashboard-addresses",
            addresses,
            (address) => {

                const location = [
                    address.address_line1,
                    address.city,
                    address.state,
                    address.country,
                ]
                    .filter(Boolean)
                    .join(", ");

                return `
                    <a
                        href="${frappe.utils.escape_html(
                            address.url
                        )}"
                        class="dashboard-list-item"
                    >

                        <div class="dashboard-list-item-icon">

                            <svg class="icon icon-sm">
                                <use href="#icon-map-pin"></use>
                            </svg>

                        </div>

                        <div class="dashboard-list-item-content">

                            <strong>
                                ${frappe.utils.escape_html(
                                    address.address_title ||
                                    address.name
                                )}
                            </strong>

                            <span>
                                ${frappe.utils.escape_html(
                                    location
                                )}
                            </span>

                        </div>

                        <div class="dashboard-list-item-value">

                            ${
                                address.is_primary_address
                                    ? `
                                        <span
                                            class="dashboard-list-status"
                                        >
                                            Primary
                                        </span>
                                    `
                                    : ""
                            }

                        </div>

                        <svg class="icon icon-sm dashboard-list-arrow">
                            <use href="#icon-chevron-right"></use>
                        </svg>

                    </a>
                `;
            },
            "No saved addresses found."
        );
    }
    function renderDashboardShipments(shipments) {

        renderDashboardList(
            "customer-dashboard-shipments",
            shipments,
            (shipment) => `
                <a
                    href="${frappe.utils.escape_html(
                        shipment.url
                    )}"
                    class="dashboard-list-item"
                >

                    <div class="dashboard-list-item-icon">

                        <svg class="icon icon-sm">
                            <use href="#icon-truck"></use>
                        </svg>

                    </div>

                    <div class="dashboard-list-item-content">

                        <strong>
                            ${frappe.utils.escape_html(
                                shipment.name
                            )}
                        </strong>

                        <span>
                            ${frappe.utils.escape_html(
                                shipment.posting_date || ""
                            )}
                        </span>

                    </div>

                    <div class="dashboard-list-item-value">

                        <strong>
                            ${frappe.format(
                                shipment.grand_total,
                                {
                                    fieldtype: "Currency",
                                    options: shipment.currency,
                                }
                            )}
                        </strong>

                        <span class="dashboard-list-status">
                            ${frappe.utils.escape_html(
                                shipment.status || ""
                            )}
                        </span>

                    </div>

                    <svg class="icon icon-sm dashboard-list-arrow">
                        <use href="#icon-chevron-right"></use>
                    </svg>

                </a>
            `,
            "No shipments found."
        );
    }

    function renderDashboardList(
        elementId,
        items,
        renderItem,
        emptyMessage
    ) {
        const container =
            document.getElementById(elementId);

        if (!container) {
            return;
        }

        if (!items.length) {
            container.innerHTML = `
                <div class="dashboard-list-empty">
                    ${frappe.utils.escape_html(emptyMessage)}
                </div>
            `;

            return;
        }

        container.innerHTML = items
            .slice(0, 5)
            .map(renderItem)
            .join("");
    }
    function renderDashboardListError(elementId) {

        const container =
            document.getElementById(elementId);

        if (!container) {
            return;
        }

        container.innerHTML = `
            <div class="dashboard-list-empty">
                Unable to load this information.
            </div>
        `;
    }
    function setDashboardMoreLink(
        elementId,
        section
    ) {
        const link =
            document.getElementById(elementId);

        if (!link || !section) {
            return;
        }

        link.href = section.more_url || "#";

        link.textContent =
            section.count > 5
                ? `View all (${section.count})`
                : "View all";
    }
    async function loadCustomerDashboardLists() {
        const customerName = dashboard.dataset.customer;

        if (!customerName) {
            return;
        }

        try {
            const response = await frappe.call({
                method:
                    "dt_ecommerce.api.customer_account.get_customer_dashboard",

                args: {
                    customer_name: customerName,
                },
            });

            const result = response.message;

            if (!result?.success) {
                throw new Error(
                    "Unable to load customer dashboard."
                );
            }

            const data = result.data || {};

            renderDashboardOrders(
                data.orders?.items || []
            );

            renderDashboardAddresses(
                data.addresses?.items || []
            );

            renderDashboardShipments(
                data.shipments?.items || []
            );
            setDashboardMoreLink(
                "customer-dashboard-orders-more",
                data.orders
            );

            setDashboardMoreLink(
                "customer-dashboard-addresses-more",
                data.addresses
            );

            setDashboardMoreLink(
                "customer-dashboard-shipments-more",
                data.shipments
            );

        } catch (error) {

            console.error(
                "Failed to load dashboard lists:",
                error
            );

            renderDashboardListError(
                "customer-dashboard-orders"
            );

            renderDashboardListError(
                "customer-dashboard-addresses"
            );

            renderDashboardListError(
                "customer-dashboard-shipments"
            );
        }
    }
    frappe.ready(() => {
     loadCustomerDashboardLists();
    })
})();