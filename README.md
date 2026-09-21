# ESPHome Custom Web Server

[![Tested with ESPHome version](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2Fsylphrena0%2Fesphome-custom-web-server%2Fmain%2Fpyproject.toml&query=%24%5B%27dependency-groups%27%5D.dev%5B0%5D&label=tested%20with&logo=esphome)](pyproject.toml)

An [ESPHome external component](https://esphome.io/components/external_components.html) that serves your own web page at a path on the device's HTTP server, next to (or instead of) the stock [`web_server`](https://esphome.io/components/web_server.html) UI.

The page can be:

- **embedded:** an HTML file stored in flash, gzipped at build time. Works with no internet access.
- **remote:** a small page stored in flash that loads your script and stylesheets from a URL. Uses almost no flash, but the browser needs internet access. With `local: true`, they're downloaded at build time and embedded instead.

## Usage

```yaml
external_components:
  - source: github://sylphrena0/esphome-custom-web-server@main
    components: [custom_web_server]

web_server:
  version: 3

custom_web_server:
  - path: /ui
    html: ui/index.html
```

With several pages, add more entries to the list.

### Options

- **path** (_Required_, string): URL path to serve the page at. Must start with `/`. Use `/` to replace `web_server`'s page.
- **auth** (_Optional_, boolean): Require `web_server`'s `auth` credentials for this page. When left out, the page is protected if `web_server` has `auth` and public otherwise. Setting it to `true` without `auth` under `web_server` is an error. Set it to `false` to make the page public even when `web_server` has `auth`.

Exactly one of:

- **html** (_Optional_, file): HTML file to embed. Inline your JavaScript and CSS into it.
- **js_url** (_Optional_, URL): Script to load, as `<script type=module>`. Scripts loaded as modules from another origin need CORS headers, which jsDelivr and GitHub Pages send.

Only with `js_url`:

- **css_url** (_Optional_, URL or list of URLs): Stylesheets to load.
- **title** (_Optional_, string): Page title.
- **body** (_Optional_, string): HTML placed in `<body>` before the script, e.g. mount point for your custom UI.
- **local** (_Optional_, boolean): Download `js_url` and `css_url` at build time and inline them into the page, so it works without internet access (like `web_server`'s `local`). Uses flash for the files, gzipped. The script must be a single bundled file: paths relative to `js_url` break once inlined. Defaults to `false`.

### Examples

#### Remote assets from github

```yaml
custom_web_server:
  - path: / # overrides esphome webserver
    title: Custom Web Server
    js_url: https://cdn.jsdelivr.net/gh/you/your-ui@v1.0.0/dist/app.js
    css_url: https://cdn.jsdelivr.net/gh/you/your-ui@v1.0.0/dist/style.css
```

#### Remote assets from github releases

```yaml
custom_web_server:
  - path: /app # does not override esphome webserver
    js_url: https://github.com/you/your-ui/releases/latest/download/app.js
    css_url: https://github.com/you/your-ui/releases/latest/download/style.css
    body: <custom-app></custom-app> # change to whatever your js/css expects
    local: true # cannot load dynamically due to CORS
```

Use this if you are compiling a dashboard and wish to use files from your releases instead of js/css committed to main.

## Caching

Each response carries an `ETag` (a hash of the page) and `Cache-Control: no-cache`: browsers check with the device on every load, and get an empty `304 Not Modified` unless the firmware changed.

## Supported platforms

Built in CI for ESP32 (ESP-IDF) and ESP8266 (Arduino), and tested with the ESPHome version in the badge above. Other platforms with `web_server_base` should work but are untested. The component uses internal ESPHome APIs, so newer/older versions of ESPHome may not work.

## Development

Requires [PDM](https://pdm-project.org): `pipx install pdm`

```sh
make install # install ESPHome and ruff into .venv
make config # validate the test configs
make build # compile the test configs
```
