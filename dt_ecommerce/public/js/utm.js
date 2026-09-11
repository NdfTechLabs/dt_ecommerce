function capture_utm_parameters() {
	const params = new URLSearchParams(window.location.search);

	[
		'utm_source',
		'utm_medium',
		'utm_campaign',
		'utm_content',
		'utm_term'
	].forEach(key => {
		const value = params.get(key);

		if (value) {
			localStorage.setItem(key, value);
		}
	});
}

capture_utm_parameters();