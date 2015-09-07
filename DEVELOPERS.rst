General tips
============

Next you can find some general VAC Templater development tips. These are only
useful for developers when setting up their Vagrant-based development
environment.

- A Varnish Plus license is required to setup the development environment. The
  Vagrantfile of the project assumes the following environment variables are
  defined:
  
  * ``VARNISH_PLUS_USER``, including the username of your Varnish Plus license.
  * ``VARNISH_PLUS_PASSWORD``, including the password if your Varnish Plus license.
  * ``VARNISH_PLUS_VAC_LICENSE``, including the location of your Varnish Administration Console license.

- Set ``global > development`` to ``true`` and ``uwsgi > daemonize`` to
  ``false`` in your personal configuration
  (``/vagrant/extras/envs/dev/vac-templater.conf``).

- Initialize database schema::

    $ python /vagrant/vac_templater/runner.py syncdb
    $ python /vagrant/vac_templater/runner.py migrate
    $ python /vagrant/vac_templater/runner.py createcachetable

- Remember the service is started using the following command::

    $ python /vagrant/vac_templater/runner.py start

- Remember .po files can be regenerated and compiled using the following
  commands::

    $ python vac_templater/runner.py makemessages -l es -e "html,txt,email,py"
    $ python vac_templater/runner.py makemessages -l es -d djangojs
    $ python vac_templater/runner.py compilemessages

- Remember a utility script (``extras/envs/dev/vac.py``) is provided in order to
  automate deployments of the sample VCL file (``extras/envs/dev/default.vcl``)
  using the VAC API.

- Remember the project contains some git subtrees::

    # Required remotes.
    $ git remote add -f --no-tags twitter-bootstrap https://github.com/twbs/bootstrap-sass.git

    # Required subtrees.
    $ git subtree add --prefix extras/resources/bootstrap/default twitter-bootstrap v3.3.4 --squash

    # Subtree update example. BEWARE of local customizations!
    $ git fetch --no-tags --prune twitter-bootstrap
    $ git subtree pull --prefix extras/resources/bootstrap/default twitter-bootstrap v3.3.5 --squash

Packaging
=========

VAC Templater sources require a build step previous to the generation of the Python
source distribution package. During this phase SASS sources are compiled to CSS,
some Javascript and CSS bundles are created, static contents are versioned,
translation files are compiled, etc.

In order to execute this site building phase and then generate the Python source
distribution package, simply run the following command in the root folder of the
VAC Templater sources::

    $ make sdist
