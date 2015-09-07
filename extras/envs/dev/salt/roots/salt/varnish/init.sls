varnish.4.0-plus-repository:
  pkgrepo.managed:
    - humanname: Varnish 4.0 Plus
    - name: deb https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@repo.varnish-software.com/ubuntu/ trusty varnish-4.0-plus
    - file: /etc/apt/sources.list.d/varnish.list
    - enabled: 1
    - key_url: https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@repo.varnish-software.com/GPG-key.txt
    - require_in:
      - pkg: varnish.packages
    - require:
      - sls: global

varnish.4.0-plus-non-free-repository:
  pkgrepo.managed:
    - humanname: Varnish 4.0 Plus VAC
    - name: deb https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@repo.varnish-software.com/ubuntu/ trusty non-free
    - file: /etc/apt/sources.list.d/varnish.list
    - enabled: 1
    - key_url: https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@repo.varnish-software.com/GPG-key.txt
    - require_in:
      - pkg: varnish.packages
    - require:
      - sls: global

varnish.4.0-repository:
  pkgrepo.managed:
    - humanname: Varnish 4.0
    - name: deb https://repo.varnish-cache.org/ubuntu/ trusty varnish-4.0
    - file: /etc/apt/sources.list.d/varnish.list
    - enabled: 1
    - key_url: https://repo.varnish-cache.org/GPG-key.txt
    - require_in:
      - pkg: varnish.packages
    - require:
      - sls: global

varnish.mongod-repository:
  pkgrepo.managed:
    - humanname: MongoDB
    - name: deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse
    - enabled: 1
    - keyid: 7F0CEB10
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: varnish.packages
    - require:
      - sls: global

/etc/apt/preferences.d/varnish:
  file.managed:
    - source: salt://varnish/apt-preferences
    - user: root
    - group: root
    - mode: 644

varnish.packages:
  pkg.installed:
    - refresh: True
    - pkgs:
      - varnish-plus
      - varnish-plus-vmods
      - vac
      - varnish-agent
    - require:
      - file: /etc/apt/preferences.d/varnish

{% for file in ['agent_secret', 'secret'] %}
/etc/varnish/{{ file }}:
  file.managed:
    - user: varnish
    - group: varnish
    - mode: 600
    - require:
      - pkg: varnish.packages
{% endfor %}

/var/lib/varnish-agent/boot.vcl:
  file.copy:
    - source: /vagrant/extras/envs/dev/default.vcl
    - user: varnish
    - group: varnish
    - mode: 644
    - force: False

varnish.varnish-service:
  service.running:
    - name: varnish
    - require:
      - pkg: varnish.packages
      - file: /var/lib/varnish-agent/boot.vcl
    - watch:
      - file: /etc/default/varnish

/etc/default/varnish:
  file.managed:
    - source: salt://varnish/varnish
    - user: root
    - group: root
    - mode: 644
    - require:
      - pkg: varnish.packages

varnish.mongod-service:
  service.running:
    - name: mongodb
    - require:
      - pkg: varnish.packages

varnish.vac-service:
  service.running:
    - name: vac
    - require:
      - pkg: varnish.packages
    - watch:
      - file: varnish.vac-settings

varnish.vac-settings:
  file.replace:
    - name: /opt/vac/etc/defaults
    - pattern: '^vacListeningPort=[0-9]+'
    - repl: 'vacListeningPort=8000'
    - require:
      - pkg: varnish.packages

varnish.vac-license:
  cmd.run:
    - name: curl -u vac:vac -i -F file=@/home/vagrant/vac-license.dat http://localhost:8000/api/v1/license/upload
    - creates: /var/opt/vac/license.vac
    - require:
      - service: varnish.vac-service

varnish.varnish-agent-service:
  service.running:
    - name: varnish-agent
    - require:
      - pkg: varnish.packages
    - watch:
      - file: varnish.varnish-agent-settings

varnish.varnish-agent-settings:
  file.replace:
    - name: /etc/default/varnish-agent
    - pattern: '^DAEMON_OPTS="[^"]*"'
    - repl: 'DAEMON_OPTS="-z http://127.0.0.1:8000/api/rest/register"'
    - require:
      - pkg: varnish.packages
