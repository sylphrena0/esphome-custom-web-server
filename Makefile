CONFIGS := tests/esp32-idf.yaml tests/esp8266.yaml
ESPHOME := pdm run esphome

.PHONY: install config build lint format clean

install:
	pdm install

config:
	@for c in $(CONFIGS); do $(ESPHOME) config $$c > /dev/null || exit 1; echo "$$c: ok"; done

build:
	@for c in $(CONFIGS); do $(ESPHOME) compile $$c || exit 1; done

lint:
	pdm run ruff check components
	pdm run ruff format --check components

format:
	pdm run ruff check --fix components
	pdm run ruff format components

clean:
	rm -rf tests/.esphome
