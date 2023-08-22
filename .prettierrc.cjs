// TODO: switch back to YAML once https://github.com/prettier/prettier/issues/15141 (I assume) is fixed
//       or at least switch to mjs once https://github.com/prettier/prettier-vscode/issues/3066 is fixed

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
