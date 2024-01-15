/**
 * This JS is only included when the RTD Sphinx search is active.
 */

// wire up the search key combination
addEventListener(
    "keydown",
    ({ key, metaKey, ctrlKey }) => {
        if (key === "k" && (metaKey || ctrlKey)) {
            if (isModalVisible()) {
                removeSearchModal()
            } else {
                showSearchModal()
            }
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
    search_button.addEventListener("click", () => showSearchModal())
}
