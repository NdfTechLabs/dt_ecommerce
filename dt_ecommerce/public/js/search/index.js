frappe.ready(function () {

    const items = window.SEARCH_ITEMS || [];
    const settings = window.WEBSHOP_SETTINGS || {};

    const $container = $("#search-product-grid");

    if (!items.length) {
        $("#search-no-results").removeClass("hidden");
        return;
    }

    new webshop.ProductGrid({
        items: items,
        settings: settings,
        products_section: $container,
        preference: "Grid View"
    });

});