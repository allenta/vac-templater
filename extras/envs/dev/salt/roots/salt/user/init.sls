user.color-prompt:
  file.replace:
    - name: /home/vagrant/.bashrc
    - pattern: '#force_color_prompt=yes'
    - repl: 'force_color_prompt=yes'

user.default-virtualenv:
  file.append:
    - name: /home/vagrant/.bashrc
    - text: source ~/virtualenvs/default/bin/activate

user.vac-templater-conf:
  file.append:
    - name: /home/vagrant/.bashrc
    - text: export VAC_TEMPLATER_CONF=/vagrant/extras/envs/dev/vac-templater.conf

user.yuicompressor-path:
  file.append:
    - name: /home/vagrant/.bashrc
    - text: export YUICOMPRESSOR_PATH=/usr/share/yui-compressor/yui-compressor.jar

user.vac-templater-cron:
  cron.present:
    - user: vagrant
    - name: /vagrant/vac_templater/runner.py cron > /dev/null 2>&1
    - minute: 1
