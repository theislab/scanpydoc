/** @type {import("prettier").Config} */
module.exports = {
    plugins: [require.resolve("prettier-plugin-jinja-template")],
    overrides: [
        {
            files: ["settings.json"],
            options: {
                parser: "json5",
                quoteProps: "preserve",
                singleQuote: false,
                trailingComma: "all",
            },
        },
        {
            files: ["*.html"],
            options: {
                parser: "jinja-template",
            },
        },
    ],
};
