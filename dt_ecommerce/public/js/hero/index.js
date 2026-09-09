frappe.ready(() => {

    document.querySelectorAll("[data-hero-slider]").forEach((slider) => {

        const slides = slider.querySelectorAll(".dt-hero-slide");
        const prev = slider.querySelector("[data-hero-prev]");
        const next = slider.querySelector("[data-hero-next]");

        // Nothing to do if there are no slides
        if (!slides.length) {
            return;
        }

        let current = 0;
        let autoplayTimer = null;
        let isPaused = false;

        const AUTOPLAY_DELAY = 5000;

        // ---------------------------------------------------------
        // Show slide
        // ---------------------------------------------------------

        function showSlide(index) {

            slides.forEach((slide, i) => {
                slide.classList.toggle("active", i === index);
            });

            current = index;
        }

        // ---------------------------------------------------------
        // Move to next slide
        // ---------------------------------------------------------

        function nextSlide() {

            showSlide((current + 1) % slides.length);

        }

        // ---------------------------------------------------------
        // Move to previous slide
        // ---------------------------------------------------------

        function prevSlide() {

            showSlide(
                (current - 1 + slides.length) % slides.length
            );

        }

        // ---------------------------------------------------------
        // Clear autoplay timer
        // ---------------------------------------------------------

        function clearAutoplay() {

            if (autoplayTimer !== null) {

                clearTimeout(autoplayTimer);

                autoplayTimer = null;
            }

        }

        // ---------------------------------------------------------
        // Schedule next slide
        // ---------------------------------------------------------

        function scheduleAutoplay() {

            clearAutoplay();

            if (isPaused || slides.length <= 1) {
                return;
            }

            autoplayTimer = setTimeout(() => {

                nextSlide();

                scheduleAutoplay();

            }, AUTOPLAY_DELAY);
        }

        // ---------------------------------------------------------
        // Manual navigation
        // ---------------------------------------------------------

        next?.addEventListener("click", () => {

            nextSlide();

            scheduleAutoplay();

        });

        prev?.addEventListener("click", () => {

            prevSlide();

            scheduleAutoplay();

        });

        // ---------------------------------------------------------
        // Pause when hovering
        // ---------------------------------------------------------

        slider.addEventListener("mouseenter", () => {

            isPaused = true;

            clearAutoplay();

        });

        // ---------------------------------------------------------
        // Resume when leaving
        // ---------------------------------------------------------

        slider.addEventListener("mouseleave", () => {

            isPaused = false;

            scheduleAutoplay();

        });

        // ---------------------------------------------------------
        // Initial slide
        // ---------------------------------------------------------

        showSlide(0);

        // Start autoplay
        scheduleAutoplay();

    });

});