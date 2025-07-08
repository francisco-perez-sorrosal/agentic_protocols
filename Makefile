.PHONY: all pixi-install build-wheel install-wheel full-setup alice bob

# Run all steps in sequence
full-setup: pixi-install build-wheel install-wheel

install:
	pixi install

build-wheel:
	pixi run build-wheel

install-wheel:
	pixi run install-wheel

alice:
	beeai delete alice
	beeai add -v ./alice

bob:
	beeai delete bob
	beeai add -v ./bob

client:
	pixi run client-test $(ARGS)

all: full-setup 
