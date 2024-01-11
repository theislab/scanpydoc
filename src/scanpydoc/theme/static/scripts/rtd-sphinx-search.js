/**
 * This JS is only included when the RTD Sphinx search is active.
 */

/** @type {HTMLDivElement} */
const search_backdrop = document.querySelector(".search__backdrop")
search_backdrop.style.zIndex = "1020"

/** @type {HTMLButtonElement} */
const search_button = document.querySelector("button[aria-label='Search']")
search_button.addEventListener("click", () => {
    showSearchModal()

    // delete the theme’s search popup
    const theme_popup = document.querySelector(".search-button__wrapper")
    if (theme_popup) theme_popup.parentElement.removeChild(theme_popup)
})
