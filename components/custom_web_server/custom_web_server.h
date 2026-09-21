#pragma once

#include "esphome/core/defines.h"
#if defined(USE_NETWORK) && !defined(USE_ZEPHYR)

#include "esphome/components/web_server_base/web_server_base.h"
#include "esphome/core/component.h"

namespace esphome::custom_web_server {

/// Serves one gzipped page, embedded at build time, at a fixed path on web_server_base's HTTP server.
class CustomWebServer : public Component, public AsyncWebHandler {
 public:
  CustomWebServer(web_server_base::WebServerBase *base, const char *path, const uint8_t *data, size_t size,
                  const char *etag, bool auth)
      : base_(base), path_(path), data_(data), size_(size), etag_(etag), auth_(auth) {}

  void setup() override;
  void dump_config() override;
  float get_setup_priority() const override;

  bool canHandle(AsyncWebServerRequest *request) const override;
  void handleRequest(AsyncWebServerRequest *request) override;

 protected:
  bool is_not_modified_(AsyncWebServerRequest *request) const;
  void send_not_modified_(AsyncWebServerRequest *request) const;

  web_server_base::WebServerBase *base_;
  const char *path_;
  const uint8_t *data_;
  size_t size_;
  const char *etag_;
  bool auth_;
};

}  // namespace esphome::custom_web_server

#endif
