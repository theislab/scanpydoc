/**
 * See https://docs.readthedocs.com/platform/stable/addons.html#integrate-with-search-as-you-type
 */

document.addEventListener("readthedocs-addons-data-ready", (event) => {
    const { addons } = event.detail.data()
    if (!addons.search?.enabled) {
        return
    }

    // wire up the search key combination
    addEventListener(
        "keydown",
        ({ key, metaKey, ctrlKey }) => {
            if (key === "k" && (metaKey || ctrlKey)) {
                const here = document.querySelector("readthedocs-search")?.show
                const event = new CustomEvent(
                    `readthedocs-search-${here ? "hide" : "show"}`,
                )
                document.dispatchEvent(event)
            }
        },
        { passive: true },
    )

    // start attempting to override the search popup and to wire up the search button
    setTimeout(overrideSearch, 0)

    function overrideSearch() {
        /** @type {HTMLDivElement} */
        const theme_popup = document.querySelector(".search-button__wrapper")
        /** @type {HTMLButtonElement} */
        const search_button = document.querySelector("button[aria-label='Search']")
        if (!theme_popup || !search_button) {
            // try again later
            setTimeout(overrideSearch, 500)
            return
        }
        // Hide the pydata theme’s search popup.
        theme_popup.style.display = "none"
        // wire up the search button
        search_button.addEventListener("click", () => {
            const event = new CustomEvent("readthedocs-search-show")
            document.dispatchEvent(event)
        })
    }
})
