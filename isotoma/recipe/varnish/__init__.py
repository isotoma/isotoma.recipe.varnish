# Copyright 2010 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" This is a module for buildout:

http://pypi.python.org/pypi/zc.buildout

This writes configuration files for varnish:

http://varnish-cache.org/

This script assumes you have varnish already installed. """

__author__ = "Doug Winter"

import logging
import os
import shutil
import sys
import sets

from Cheetah.Template import Template

import zc.buildout
from isotoma.recipe import gocaptain

class Varnish(object):

    """ Buildout class for Varnish """

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout
        self.logger = logging.getLogger(self.name)

        self.options["location"] = os.path.join(
                buildout["buildout"]["parts-directory"], self.name)

        # Set some default options
        self.options.setdefault("cache-size", "1G")
        self.options.setdefault("daemon", "/usr/sbin/varnishd")
        self.options.setdefault("runtime-parameters","")
        self.options.setdefault('verbose-headers', 'off')
        self.options.setdefault("template", os.path.join(os.path.dirname(__file__), "template.vcl"))
        self.options.setdefault("config", os.path.join(self.options["location"], "varnish.vcl"))
        self.options.setdefault("connect-timeout", "0.4s")
        self.options.setdefault("first-byte-timeout", "300s")
        self.options.setdefault("between-bytes-timeout", "60s")
        self.options.setdefault("cache-size", "80M")
        self.options.setdefault("user", "nobody")
        self.options.setdefault("group", "nobody")

    def install(self):
        location=self.options["location"]
        if not os.path.exists(location):
            os.mkdir(location)
        self.options.created(location)
        self.add_runner()
        self.create_config()
        if "varnishlog" in self.options:
            self.add_log()
        return self.options.created()

    def update(self):
        pass

    def add_runner(self):
        template = self.options['template']
        target=os.path.join(self.buildout["buildout"]["bin-directory"],self.name)
        f=open(target, "wt")
        pidfile = os.path.join(self.buildout['buildout']['directory'], "var", self.name + ".pid")
        storage = os.path.join(self.buildout["buildout"]['directory'], 'var', self.name + ".storage")
        args = """
            -p user=%(user)s
            -p group=%(group)s
            -f "%(config)s"
            -P "%(pidfile)s
            -a %(bind)s
            -s file,"%(storage)s",%(cache-size)s
        """ % { 'user': self.options['user'],
                'group': self.options['group'],
                'config': self.options['config'],
                'pidfile': pidfile,
                'bind': self.options['bind'],
                'storage': storage,
                'cache-size': self.options['cache-size'],

                }
        if "telnet" in self.options:
            args += "-T %s\n" % self.options['telnet']
        if "name" in self.options:
            args += "-n %s\n" % self.options['name']
        for parameter in self.options.get('parameters', "").split():
            args += "-p %s\n" % (parameter,)
        gc = gocaptain.Automatic()
        gc.write(f,
                 daemon = self.options['daemon'],
                 args=args,
                 pidfile=pidfile,
                 name=self.name,
                 description="%s daemon" % self.name,
                 )
        f.close()
        os.chmod(target, 0755)
        self.options.created(target)

    def add_log(self):
        target=os.path.join(self.buildout["buildout"]["bin-directory"],self.name + "log")
        f = open(target, "wt")
        pidfile = os.path.join(self.options["location"], "varnishlog.pid")
        daemon = self.options['varnishlog']

        args = """
            -a
            -D
            -w "%s"
            -P "%s"
            """% (self.options["logfile"], pidfile)
        if "name" in self.options:
            args += '-n "%s"\n' % self.options["name"]
        if "log-include-regex" in self.options:
            args += '-I "%s"\n' % self.options["log-include-regex"]
        if "log-exclude-regex" in self.options:
            args += '-X "%s"\n' % self.options["log-exclude-regex"]
        if "log-include-tag" in self.options:
            args += '-i "%s"' % self.options["log-include-tag"]
        if "log-exclude-tag" in self.options:
            args += '-x "%s"\n' % self.options["log-exclude-tag"]
        gc = gocaptain.Automatic()
        gc.write(f,
                 daemon=daemon,
                 args=args,
                 pidfile=pidfile,
                 name=self.name + "log",
                 description="%s logging daemon" % self.name,
                 )
        f.close()
        os.chmod(target, 0755)
        self.options.created(target)

    def create_config(self):
        template = self.options["template"]
        config = self.options["config"]
        backends = self.options["backends"]
        vars = self.options.copy()
        vars['backends'] = [{'ID': id, 'host': host, 'port': port} for id, (host, port) in enumerate([x.split(":") for x in backends.strip().split()])]
        for k, v in vars.items():
            if '-' in k:
                vars[k.replace('-', '_')] = v;
                del vars[k]
        c = Template(open(template).read(), searchList=vars)
        open(config, "w").write(str(c))
        self.options.created(self.options["config"])
