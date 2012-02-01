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
import subprocess
import re

try:
    from hashlib import sha1
except ImportError:
    import sha
    def sha1(str):
        return sha.new(str)

from Cheetah.Template import Template

import zc.buildout
from isotoma.recipe import gocaptain

varnishadm = """
#! /usr/bin/env python
import os, sys
args = ["/usr/bin/varnishadm", "-T", "%(port)s"] + sys.argv[1:]
if not os.path.exists(args[0]):
    print "Could not find varnishadm, is varnish installed?"
    sys.exit(1)
os.execvp(args[0], args)
""".lstrip()

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
        self.options.setdefault("template-version", "1")
        self.options.setdefault("config", os.path.join(self.options["location"], "varnish.vcl"))
        self.options.setdefault("connect-timeout", "0.4s")
        self.options.setdefault("first-byte-timeout", "300s")
        self.options.setdefault("between-bytes-timeout", "60s")
        self.options.setdefault("cache-size", "80M")
        self.options.setdefault("user", "nobody")
        self.options.setdefault("group", "nobody")
        self.options.setdefault("cachehtml", "off")
        self.options.setdefault("enable-passthru", "off")

        major, minor = self.determine_varnish_version()
        if major != '2':
            raise zc.buildout.UserError("Only version 2 of Varnish is supported")

        self.options["major"] = major
        self.options["minor"] = minor

        # Record a SHA1 of the template we use, so we can detect changes in subsequent runs
        self.options["__hashes_template"] = sha1(open(self.options["template"]).read()).hexdigest()

    def determine_varnish_version(self):
        p = subprocess.Popen([self.options["daemon"], "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        match = re.search("varnish-(?P<major>\d+)\.(?P<minor>\d+)", stderr)
        return match.group('major'), match.group('minor')

    def downgrade_config_to_2_0(self, template):
        # Downgrade 'return (pass);' to 'pass;'
        for ret in ("pass", "pipe", "lookup", "hash", "deliver", "fetch", "deliver", "esi", "discard", "keep"):
            pattern = "return\w*\(%s\)" % ret
            template = re.sub(pattern, ret, template)
        # Replace all occurences of beresp with obj
        template = template.replace("beresp", "obj")
        return template

    def install(self):
        location=self.options["location"]
        if not os.path.exists(location):
            os.mkdir(location)
        self.options.created(location)
        self.add_runner()
        self.create_config()

        if "telnet" in self.options:
            self.add_varnishadm()
            if "name" in self.options:
                self.add_varnish_tool()

        if "varnishlog" in self.options:
            self.add_log()
        return self.options.created()

    def update(self):
        pass

    def add_runner(self):
        template = self.options['template']
        target=os.path.join(self.buildout["buildout"]["bin-directory"],self.name)
        f=open(target, "wt")

        if 'run-directory' in self.buildout['buildout']:
            pidfile = os.path.join(self.buildout['buildout']['run-directory'], self.name + ".pid")
        else:
            pidfile = os.path.join(self.buildout['buildout']['directory'], "var", self.name + ".pid")

        storage = os.path.join(self.buildout["buildout"]['directory'], 'var', self.name + ".storage")
        args = """
            -p user=%(user)s
            -p group=%(group)s
            -f "%(config)s"
            -P "%(pidfile)s"
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

    def add_varnishadm(self):
        target = os.path.join(self.buildout["buildout"]["bin-directory"], self.name+"adm")
        f = open(target, "w")
        f.write(varnishadm % dict(port=self.options['telnet']))
        f.close()
        os.chmod(target, 0755)
        self.options.created(target)

    def add_varnish_tool(self):
        path = self.buildout["buildout"]["bin-directory"]
        egg_paths = [
            self.buildout["buildout"]["develop-eggs-directory"],
            self.buildout["buildout"]["eggs-directory"],
            ]

        args = ",".join(["'%s'" % self.options[x] for x in ('name', 'telnet', 'config')])

        ws = zc.buildout.easy_install.working_set(["isotoma.recipe.varnish"], sys.executable, egg_paths)
        zc.buildout.easy_install.scripts([(self.name+"ctl", "isotoma.recipe.varnish.varnishtool", "run")], ws, sys.executable, path, arguments=args)
        self.options.created(os.path.join(path, self.name+"ctl"))

    def add_log(self):
        target=os.path.join(self.buildout["buildout"]["bin-directory"],self.name + "log")
        f = open(target, "wt")

        if 'run-directory' in self.buildout['buildout']:
            pidfile = os.path.join(self.buildout['buildout']['run-directory'], self.name + "log.pid")
        else:
            pidfile = os.path.join(self.buildout['buildout']['directory'], "var", self.name + "log.pid")

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

    def get_config(self):
        template = open(self.options["template"]).read()

        varnish_ver = int(self.options["minor"])
        template_ver = int(self.options["template-version"])

        if varnish_ver < template_ver:
            #FIXME: This needs to be smarter if we ever can dowgrade multiple versions
            template = self.downgrade_config_to_2_0(template)
        elif varnish_ver > template_ver:
            raise zc.buildout.UserError("Cannot upgrade template version")

        return template

    def handle_boolean(self, args, name):
            if args[name].lower() in ('on', 'yes', 'true', '1'):
                args[name] = True
            else:
                args[name] = False

    def create_config(self):
        template = self.options["template"]
        config = self.options["config"]
        backends = self.options["backends"]
        vars = self.options.copy()
        vars['backends'] = [{'ID': id, 'host': host, 'port': port} for id, (host, port) in enumerate([x.split(":") for x in backends.strip().split()])]
        self.handle_boolean(vars, 'verbose-headers')
        self.handle_boolean(vars, 'cachehtml')
        self.handle_boolean(vars, 'enable-passthru')
        for k, v in vars.items():
            if '-' in k:
                vars[k.replace('-', '_')] = v;
                del vars[k]
        c = Template(self.get_config(), searchList=vars)
        open(config, "w").write(str(c))
        self.options.created(self.options["config"])

