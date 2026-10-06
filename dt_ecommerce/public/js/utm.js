function setCookie(name, value, maxAge = 31536000) {
    document.cookie =
        `${encodeURIComponent(name)}=${encodeURIComponent(value)}; ` +
        `path=/; ` +
        `max-age=${maxAge}; ` +
        `SameSite=Lax`;
}


function getCookie(name) {
    const encodedName = encodeURIComponent(name) + "=";

    const cookies = document.cookie.split(";");

    for (const cookie of cookies) {
        const value = cookie.trim();

        if (value.startsWith(encodedName)) {
            return decodeURIComponent(
                value.substring(encodedName.length)
            );
        }
    }

    return null;
}

function generateVisitorId() {
    if (crypto.randomUUID) {
        return crypto.randomUUID();
    }

    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);

    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    return [...bytes]
        .map(b => b.toString(16).padStart(2, "0"))
        .join("")
        .replace(
            /^(.{8})(.{4})(.{4})(.{4})(.{12})$/,
            "$1-$2-$3-$4-$5"
        );
}


function getVisitorId() {
    const storageKey = "dt_visitor_id";

    let visitorId = localStorage.getItem(storageKey);

    if (!visitorId) {
        visitorId = generateVisitorId();
        localStorage.setItem(storageKey, visitorId);
    }

    setCookie("visitor_id", visitorId);

    return visitorId;
}

const UTM_KEYS = [
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term"
];

const UTM_MAX_AGE = 60 * 60 * 24 * 30; // 30 days


function clear_utm_parameters() {
    UTM_KEYS.forEach(key => {
        localStorage.removeItem(key);
        setCookie(key, "", 0);
    });
}


function capture_utm_parameters() {
    const params = new URLSearchParams(window.location.search);

    const utm = {};

    UTM_KEYS.forEach(key => {
        utm[key] = params.get(key);
    });

    const hasUtm = Object.values(utm).some(value => value);

    if (!hasUtm) {
        return;
    }

    // New attribution event → discard previous attribution
    clear_utm_parameters();

    UTM_KEYS.forEach(key => {
        const value = utm[key];

        if (!value) {
            return;
        }

        localStorage.setItem(key, value);
        setCookie(key, value, UTM_MAX_AGE);
    });
}

function initialize_tracking() {
    getVisitorId();
    capture_utm_parameters();
}

frappe.ready(() => {
		initialize_tracking();
});