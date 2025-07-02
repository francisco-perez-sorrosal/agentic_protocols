.PHONY: all pixi-install build-wheel install-wheel full-setup

# Run all steps in sequence
full-setup: pixi-install build-wheel install-wheel

pixi-install:
	pixi install

build-wheel:
	pixi run build-wheel

install-wheel:
	pixi run install-wheel

all: full-setup 