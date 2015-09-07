# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure('2') do |config|
  config.vm.box = 'ubuntu/trusty64'
  config.vm.box_version = '=14.04'
  config.vm.box_check_update = true

  config.ssh.forward_agent = true

  config.vm.provider :virtualbox do |vb|
    vb.customize [
      'modifyvm', :id,
      '--memory', '1048',
      '--natdnshostresolver1', 'off',
      '--natdnsproxy1', 'on',
      '--accelerate3d', 'off',
    ]
  end

  ##
  ## Master.
  ##
  config.vm.define :master, primary: true do |machine|
    machine.vm.hostname = 'dev'

    machine.vm.provider :virtualbox do |vb|
      vb.customize [
        'modifyvm', :id,
        '--name', 'VAC Templater',
      ]
    end

    machine.vm.provision :file, source: ENV['VARNISH_PLUS_VAC_LICENSE'], destination: '/home/vagrant/vac-license.dat'

    machine.vm.provision :salt do |salt|
      salt.pillar({
        'varnish-plus' => {
          'user' => ENV['VARNISH_PLUS_USER'],
          'password' => ENV['VARNISH_PLUS_PASSWORD'],
        },
      })

      salt.minion_config = 'extras/envs/dev/salt/minion'
      salt.run_highstate = true
      salt.verbose = true
      salt.log_level = 'info'
      salt.colorize = true
      salt.install_type = 'git'
      salt.install_args = 'v2015.2'
    end

    # /etc/hosts
    # 192.168.100.182 vac-templater.allenta.dev
    machine.vm.network :private_network, ip: '192.168.100.182'

    machine.vm.synced_folder '.', '/vagrant', :nfs => true
    machine.vm.synced_folder 'extras/envs/dev/salt/roots', '/srv', :nfs => false
  end
end
