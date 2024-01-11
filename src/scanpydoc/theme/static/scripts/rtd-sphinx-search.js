/**
 * This JS is only included when the RTD Sphinx search is active.
 */

setTimeout(overrideSearchButton, 0)

function overrideSearchButton() {
    /** @type {HTMLDivElement} */
    const search_backdrop = document.querySelector(".search__backdrop")
    if (!search_backdrop) {
        setTimeout(overrideSearchButton, 500)
        return
    }
    search_backdrop.style.zIndex = "1020"

    /** @type {HTMLButtonElement} */
    const search_button = document.querySelector("button[aria-label='Search']")
    search_button.addEventListener("click", () => {
        showSearchModal()

        // hide the theme’s search popup
        /** @type {HTMLDivElement} */
        const theme_popup = document.querySelector(".search-button__wrapper")
        theme_popup.style.display = "none"
    })
}
