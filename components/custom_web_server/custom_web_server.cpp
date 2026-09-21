#include "custom_web_server.h"
#if defined(USE_NETWORK) && !defined(USE_ZEPHYR)

#include "esphome/core/log.h"

namespace esphome::custom_web_server {

void CustomWebServer::setup() {
  this->base_->init();
  if (this->auth_) {
    this->base_->add_handler(this);  // behind web_server's auth, when it's configured
  } else {
    this->base_->add_handler_without_auth(this);
  }
}

void CustomWebServer::dump_config() {
  ESP_LOGCONFIG("custom_web_server",
                "Custom Web Server:\n"
                "  Path: %s\n"
                "  Size: %u bytes (gzipped)\n"
                "  Auth: %s",
                this->path_, static_cast<unsigned>(this->size_), YESNO(this->auth_));
}

float CustomWebServer::get_setup_priority() const { return setup_priority::WIFI - 0.5f; }

bool CustomWebServer::canHandle(AsyncWebServerRequest *request) const {
  if (request->method() != HTTP_GET)
    return false;
#ifdef USE_ESP32
  char url_buf[AsyncWebServerRequest::URL_BUF_SIZE];
  return request->url_to(url_buf) == this->path_;
#else
  return request->url() == this->path_;
#endif
}

void CustomWebServer::handleRequest(AsyncWebServerRequest *request) {
  if (this->is_not_modified_(request)) {
    this->send_not_modified_(request);
    return;
  }
#ifdef USE_ESP8266
  auto *response = request->beginResponse_P(200, "text/html", this->data_, this->size_);
#else
  auto *response = request->beginResponse(200, "text/html", this->data_, this->size_);
#endif
  response->addHeader("Content-Encoding", "gzip");
  response->addHeader("ETag", this->etag_);
  response->addHeader("Cache-Control", "no-cache");
  request->send(response);
}

bool CustomWebServer::is_not_modified_(AsyncWebServerRequest *request) const {
#ifdef USE_ESP32
  auto value = request->get_header("If-None-Match");
  return value.has_value() && value->find(this->etag_) != std::string::npos;
#else
  const AsyncWebHeader *header = request->getHeader("If-None-Match");
  return header != nullptr && header->value().indexOf(this->etag_) >= 0;
#endif
}

void CustomWebServer::send_not_modified_(AsyncWebServerRequest *request) const {
#ifdef USE_ESP32
  // web_server_idf turns status codes it doesn't know, 304 included, into a 500
  httpd_resp_set_status(*request, "304 Not Modified");
  httpd_resp_set_hdr(*request, "ETag", this->etag_);
  httpd_resp_set_hdr(*request, "Cache-Control", "no-cache");
  httpd_resp_send(*request, nullptr, 0);
#else
  auto *response = request->beginResponse(304);
  response->addHeader("ETag", this->etag_);
  response->addHeader("Cache-Control", "no-cache");
  request->send(response);
#endif
}

}  // namespace esphome::custom_web_server

#endif
