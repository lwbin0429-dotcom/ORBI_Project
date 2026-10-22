# Project instructions

@C:\Users\User\.codex\RTK.md

## Readable source formatting

Apply these rules to all existing code you change and all new code:

- Keep the application and its user-facing text in English.
- Write expanded, readable source. Do not minify or combine unrelated statements
  on one line.
- Use two spaces for HTML, CSS and JavaScript, and four spaces for Python.
- In HTML/Jinja templates, put nested elements on separate, indented lines.
  Put multiple attributes on separate lines for multiline opening tags. Preserve
  meaningful inline whitespace and Jinja expressions and control blocks.
- In CSS, put each declaration on its own line and each rule in its own block.
  Expand media queries and separate related sections with blank lines.
- In JavaScript and Python, put each statement on its own line. Wrap long calls,
  conditions, collections and argument lists across indented lines.
- Keep line lengths near 88 characters. Do not split literal strings or URLs in
  ways that change their values.
- Follow `.editorconfig` and `.prettierrc.json`. Keep formatting changes separate
  from behavior changes whenever practical.
- Use a Jinja-aware formatter or manual formatting for `src/templates/*.html`.
  These templates are excluded from generic Prettier HTML formatting to protect
  Jinja control syntax inside attributes. Python/Jinja tool settings are in
  `pyproject.toml`.
- Preserve functionality and run the relevant existing tests after formatting.
