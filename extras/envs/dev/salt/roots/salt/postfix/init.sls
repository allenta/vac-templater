postfix.packages:
  pkg.installed:
    - refresh: True
    - pkgs:
      - postfix
    - require:
      - sls: global

postfix.service:
  service.running:
    - name: postfix
    - require:
      - pkg: postfix.packages
    - watch:
      - file: /etc/mailname
      - file: /etc/postfix/main.cf

/etc/mailname:
  file.managed:
    - source: salt://postfix/mailname
    - user: root
    - group: root
    - mode: 644

/etc/postfix/main.cf:
  file.managed:
    - source: salt://postfix/main.cf
    - user: root
    - group: root
    - mode: 644
