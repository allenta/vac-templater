VAC_TEMPLATER_ROOT = $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

sdist: build
	@echo
	@echo "> Creating Python source distribution package..."
	cd $(VAC_TEMPLATER_ROOT)/build; python setup.py sdist

	@echo
	@echo "> Source distribution package successfully generated in $(VAC_TEMPLATER_ROOT)/build/dist/"
	@echo

upload: build
	cd $(VAC_TEMPLATER_ROOT)/build; python setup.py register sdist upload

build: clone
	@echo
	@echo "> Compiling .po files..."
	python "$(VAC_TEMPLATER_ROOT)/build/vac_templater/runner.py" compilemessages

	@echo
	@echo "> Generating static media..."
	python "$(VAC_TEMPLATER_ROOT)/build/vac_templater/runner.py" generatemedia

	@echo
	@echo "> Cleaning up..."
	rm -rf "$(VAC_TEMPLATER_ROOT)/build/vac_templater/static"
	find "$(VAC_TEMPLATER_ROOT)/build" \
		-name "*.pyc" -o \
		-name "*.po" | xargs rm -f

clone: clean
	@echo
	@echo "> Cloning VAC Templater source files..."
	mkdir -p "$(VAC_TEMPLATER_ROOT)/build/"
	rsync -a --delete --delete-excluded \
		--exclude="build" --exclude="extras" --exclude=".git" \
		--exclude="DEVELOPERS.rst" \
		"$(VAC_TEMPLATER_ROOT)/" "$(VAC_TEMPLATER_ROOT)/build/"

clean:
	rm -rf "$(VAC_TEMPLATER_ROOT)/build/"
	find "$(VAC_TEMPLATER_ROOT)" -name "*.pyc" -o -name "*.mo" | xargs rm -f
