global.packages:
  pkg.installed:
    - refresh: True
    - pkgs:
      - apt-transport-https
      - gettext
      - git
      - links
      - nano
      - ntp
      - python-dev
      - python-pip
      - python-software-properties
      - ruby-dev
      - sqlite3
      - yui-compressor

{% for package, version in [('sass', '3.4.14'), ('compass', '1.0.3')] %}
global.gems.{{ package }}:
  gem.installed:
    - user: root
    - name: {{ package }}
    - version: {{ version }}
{% endfor %}

global.timezone:
  timezone.system:
    - name: Europe/Madrid
    - utc: True
