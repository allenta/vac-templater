ROOT = $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)

DEFAULT_JS = \
	transition.js \
	alert.js      \
	button.js     \
	carousel.js   \
	collapse.js   \
	dropdown.js   \
	modal.js      \
	scrollspy.js  \
	tab.js        \
	tooltip.js    \
	popover.js    \
	affix.js

.PHONY : default

build = \
	@( \
		echo "> Building '$(1)' Twitter Bootstrap (CSS)..."; \
		mkdir -p "$(ROOT)/vac_templater/static/vac-templater/$(1)/css/plugins/bootstrap"; \
		cd "$(ROOT)/extras/resources/bootstrap/$(1)/assets/stylesheets/"; \
		sass --sourcemap=none _bootstrap.scss "$(ROOT)/vac_templater/static/vac-templater/$(1)/css/plugins/bootstrap/bootstrap.css"; \
		\
		echo "> Building '$(1)' Twitter Bootstrap (JS)..."; \
		mkdir -p "$(ROOT)/vac_templater/static/vac-templater/$(1)/js/plugins/bootstrap"; \
		rm -f "$(ROOT)/vac_templater/static/vac-templater/$(1)/js/plugins/bootstrap/bootstrap.js"; \
		for FILE in $(2); do \
		  cat "$(ROOT)/extras/resources/bootstrap/$(1)/assets/javascripts/bootstrap/$$FILE" >> $(ROOT)/vac_templater/static/vac-templater/$(1)/js/plugins/bootstrap/bootstrap.js; \
		done; \
		\
		echo "> Building '$(1)' Twitter Bootstrap (images)..."; \
		mkdir -p "$(ROOT)/vac_templater/static/vac-templater/$(1)/images/plugins/bootstrap"; \
		cp -R "$(ROOT)/extras/resources/bootstrap/$(1)/assets/images/"* "$(ROOT)/vac_templater/static/vac-templater/$(1)/images/plugins/bootstrap" 2>/dev/null || :; \
		\
		echo "> Building '$(1)' Twitter Bootstrap (fonts)..."; \
		mkdir -p "$(ROOT)/vac_templater/static/vac-templater/$(1)/fonts/plugins/bootstrap"; \
		cp -R "$(ROOT)/extras/resources/bootstrap/$(1)/assets/fonts/bootstrap/"* "$(ROOT)/vac_templater/static/vac-templater/$(1)/fonts/plugins/bootstrap" 2>/dev/null || :; \
	)

all: default

default:
	$(call build,default,$(DEFAULT_JS))
