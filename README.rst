Varnish buildout recipe
=======================

This package provides buildout_ recipes for the configuration of varnish.  This
has a number of features and differences from `plone.recipe.varnish`_, but it
was inspired by that package.

This package also doesn't provide all the features of plone.recipe.varnish,
since it's designed to be used slightly differently.  Using this recipe you
have one varnish daemon per deployed backend application server.  If you have
three different applications on a server, you will run three varnish daemons.
This means they can be separately deployed, configured and maintained.  This
also means there is no need for host-header based routing.

Note that this package provides no support for *installing* varnish.  Use the
binary provided by your OS, or use `zc.recipe.cmmi`_ perhaps.

The key differences are:

 1. This packages uses `isotoma.recipe.gocaptain`_ to write the start/stop scripts, so it's more likely to play well with your OS and behaves more normally
 2. Support for a separate logging system with each varnish instance, again using GoCaptain
 3. A different (and arguably more sane) basic varnish configuration
 4. Easy support for custom templates

.. _buildout: http://pypi.python.org/pypi/zc.buildout
.. _`plone.recipe.varnish`: http://pypi.python.org/pypi/plone.recipe.varnish
.. _`isotoma.recipe.gocaptain`: http://pypi.python.org/pypi/isotoma.recipe.gocaptain
.. _`zc.recipe.cmmi`: http://pypi.python.org/pypi/zc.recipe.cmmi

Configuration example
---------------------

A recipe for this package would look something like::

    [varnish]
    recipe = isotoma.recipe.varnish
    name = mysite
    bind = 127.0.0.1:8080
    backends = 127.0.0.1:9000
    varnishlog = /usr/bin/varnishncsa
    logfile = /var/log/varnish/mysite.log
    
This would create two start scripts in your bin directory: varnish and
varnishlog.  The log instance will only log activity for this varnish instance.

Mandatory Parameters
--------------------

bind
    The host:port to listen on
backends
    A list of backends (note only one backend is currently supported with the default template, because some director code is required.  A custom template should work ok though, if you write one.)

Optional Parameters
-------------------

name
    This identifies the individual varnish instance - see the -n option to varnishd. (required if you are using varnishlog and recommended even if not)
cache-size
    The size of the cache.
connect-timeout
    The .connect_timeout option in the output VCL
first-byte-timeout
    The .first_byte_timeout option in the output VCL
between-bytes-timeout
    The .between_bytes_timeout in the output VCL
daemon
    The path to the varnishd daemon (default /usr/sbin/varnishd)
parameters
    Any other parameters to pass at runtime (without the -p)
user
    The user to run the daemon as (default nobody)
group
    The group to run the daemon as (default nobody)
verbose-headers
    If you set this, you will get some very useful debugging headers in your HTTP output.
template
    The path to the template to use, if you wish to provide a different one. It's expected that this will be a Varnish 2.1 template.
    If you try to use Varnish 2.0, isotoma.recipe.varnish will attempt to downgrade the template.
log-include-regex
    Include lines matching the specified regex in the log output
log-exclude-regex
    Exclude lines matching the specified regex from the log output
log-include-tag
    Include lines with the specified tag in the log output
log-exclude-tag
    Exclude lines with the specified tag from the log output
logfile
    The path to the logfile to write (required if varnishlog specified)
varnishlog
    The path to the varnishlog binary - you can use either varnishlog or varnishncsa
telnet
    Offer a management interface on the specified address and port. (format: address:port)
    Will generate a varnishadm wrapper in bin dir with the -T address:port already provided

License
-------

Copyright 2010 Isotoma Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

