import gzip
import hashlib
import html
import re
from typing import Any

from esphome import codegen, config_validation, external_files, final_validate
from esphome.components import web_server_base
from esphome.components.web_server_base import CONF_WEB_SERVER_BASE_ID
from esphome.const import (
    CONF_AUTH,
    CONF_CSS_URL,
    CONF_ID,
    CONF_JS_URL,
    CONF_LOCAL,
    CONF_PATH,
    CONF_RAW_DATA_ID,
)

DOMAIN = "custom_web_server"

CODEOWNERS = ["@sylphrena0"]
DEPENDENCIES = ["network"]
AUTO_LOAD = ["web_server_base"]
MULTI_CONF = True

CONF_HTML = "html"
CONF_TITLE = "title"
CONF_BODY = "body"

custom_web_server_ns = codegen.esphome_ns.namespace(DOMAIN)
CustomWebServer = custom_web_server_ns.class_("CustomWebServer", codegen.Component)


def _validate_path(value):
    value = config_validation.string_strict(value)
    if not value.startswith("/"):
        raise config_validation.Invalid("path must start with '/'")
    if any(c in value for c in "?#"):
        raise config_validation.Invalid("path can't contain a query string or fragment")
    return value


def _validate_shell_options(config):
    if CONF_HTML in config:
        for key in (CONF_CSS_URL, CONF_TITLE, CONF_BODY, CONF_LOCAL):
            if key in config:
                raise config_validation.Invalid(f"'{key}' only applies with 'js_url'", path=[key])
    return config


CONFIG_SCHEMA = config_validation.All(
    config_validation.Schema(
        {
            config_validation.GenerateID(): config_validation.declare_id(CustomWebServer),
            config_validation.GenerateID(CONF_WEB_SERVER_BASE_ID): config_validation.use_id(
                web_server_base.WebServerBase
            ),
            config_validation.GenerateID(CONF_RAW_DATA_ID): config_validation.declare_id(codegen.uint8),
            config_validation.Required(CONF_PATH): _validate_path,
            # No default, so an explicit `auth: true` can be checked in _final_validate
            config_validation.Optional(CONF_AUTH): config_validation.boolean,
            config_validation.Exclusive(CONF_HTML, "source"): config_validation.file_,
            config_validation.Exclusive(CONF_JS_URL, "source"): config_validation.url,
            config_validation.Optional(CONF_CSS_URL): config_validation.ensure_list(config_validation.url),
            config_validation.Optional(CONF_TITLE): config_validation.string,
            config_validation.Optional(CONF_BODY): config_validation.string,
            config_validation.Optional(CONF_LOCAL): config_validation.boolean,
        }
    ).extend(config_validation.COMPONENT_SCHEMA),
    config_validation.has_exactly_one_key(CONF_HTML, CONF_JS_URL),
    _validate_shell_options,
)


def _final_validate(config):
    full_config: dict[str, Any] = final_validate.full_config.get()  # pyright: ignore[reportAssignmentType]
    paths = [conf[CONF_PATH] for conf in full_config[DOMAIN]]
    if paths.count(config[CONF_PATH]) > 1:
        raise config_validation.Invalid(
            f"path '{config[CONF_PATH]}' is used by more than one custom_web_server",
            path=[CONF_PATH],
        )
    if config.get(CONF_AUTH) and CONF_AUTH not in full_config.get("web_server", {}):
        raise config_validation.Invalid(
            "'auth: true' needs 'auth' credentials under 'web_server'",
            path=[CONF_AUTH],
        )
    return config


FINAL_VALIDATE_SCHEMA = _final_validate


def _download(url: str, tag: str) -> str:
    """Fetch url (cached by ESPHome, reused offline) for inlining in a <tag> element."""
    path = external_files.compute_local_file_path(DOMAIN, url)
    text = external_files.download_content(url, path).decode()
    # A literal "</script" or "</style" would end the element early
    return re.sub(f"</({tag})", r"<\\/\1", text, flags=re.IGNORECASE)


def _build_shell(config) -> bytes:
    """A minimal page that loads the UI's script and stylesheets from js_url/css_url,
    or inlines them with local: true."""
    local = config.get(CONF_LOCAL, False)
    page = "<!DOCTYPE html><html><head><meta charset=UTF-8>"
    page += "<meta name=viewport content='width=device-width, initial-scale=1'>"
    page += "<link rel=icon href=data:>"
    if CONF_TITLE in config:
        page += f"<title>{html.escape(config[CONF_TITLE])}</title>"
    for css_url in config.get(CONF_CSS_URL, []):
        if local:
            page += f"<style>{_download(css_url, 'style')}</style>"
        else:
            page += f'<link rel=stylesheet href="{html.escape(css_url)}">'
    page += "</head><body>"
    page += config.get(CONF_BODY, "")
    js_url = config[CONF_JS_URL]
    if local:
        page += f"<script type=module>{_download(js_url, 'script')}</script>"
    else:
        page += f'<script type=module src="{html.escape(js_url)}"></script>'
    page += "</body></html>"
    return page.encode()


async def to_code(config):
    if CONF_HTML in config:
        raw = config[CONF_HTML].read_bytes()
    else:
        raw = _build_shell(config)
    # mtime=0 keeps the output, and so the firmware, identical between builds
    data = gzip.compress(raw, compresslevel=9, mtime=0)
    etag = '"' + hashlib.sha256(raw).hexdigest()[:16] + '"'

    base = await codegen.get_variable(config[CONF_WEB_SERVER_BASE_ID])
    prog_arr = codegen.progmem_array(config[CONF_RAW_DATA_ID], list(data))
    var = codegen.new_Pvariable(
        config[CONF_ID],
        base,
        config[CONF_PATH],
        prog_arr,
        len(data),
        etag,
        config.get(CONF_AUTH, True),
    )
    await codegen.register_component(var, config)
