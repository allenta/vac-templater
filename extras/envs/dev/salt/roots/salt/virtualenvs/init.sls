virtualenvs.install-virtualenv:
  pip.installed:
    - name: virtualenv==1.11.5
    - user: root
    - require:
      - sls: global

virtualenvs.folder:
  file.directory:
    - name: /home/vagrant/virtualenvs
    - user: vagrant
    - group: vagrant
    - mode: 755

virtualenvs.default:
  virtualenv.managed:
    - name: /home/vagrant/virtualenvs/default
    - user: vagrant
    - requirements: /vagrant/requirements.txt
    - require:
      - pip: virtualenvs.install-virtualenv
      - file: virtualenvs.folder

{% for package in ['ipython', 'tabulate==0.7.5'] %}
virtualenvs.default.{{ package }}:
  pip.installed:
    - name: {{ package }}
    - user: vagrant
    - bin_env: /home/vagrant/virtualenvs/default
    - require:
      - virtualenv: virtualenvs.default
{% endfor %}
