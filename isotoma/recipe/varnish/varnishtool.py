
try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1

import sys, time
from telnetlib import Telnet

class Configuration(object):
    """ Information about the state of a particular VCL file that is loaded
    into Varnish. This would be a namedtuple but we still support Python 2.4
    """
    __slots__ = ("connection", "status", "count", "name")

    def __init__(self, connection, status, count, name):
        self.connection = connection
        self.status = status
        self.count = int(count)
        self.name = name

    def use(self):
        self.connection.request('vcl.use %s' % self.name)

    def discard(self):
        self.connection.request('vcl.discard %s' % self.name)


class VarnishError(Exception):
    pass


class RequestFailed(VarnishError):
    pass


class VarnishConnection(Telnet):

    def __init__(self, *args):
        Telnet.__init__(self, *args)
        self.read_until("Type 'quit' to close CLI session.\n\n")

    def request(self, command):
        self.write('%s\n' % command)

        header = '\n'
        for i in range(5):
            header = self.read_until('\n')
            if header != '\n':
                break
        else:
            raise RequestFailed("Varnish did not respond with a status code")

        status, length = map(int, header.split())

        content = ''
        while len(content) < length:
            content += self.read_until('\n')

        if status != 200:
            raise RequestFailed(content)

        return content

    def load(self, vcl, name=None):
        if not name:
            name = sha1(open(vcl).read()).hexdigest()
        if name in self.vcl_list():
            return self.vcl_list()[name]
        self.request('vcl.load %s %s' % (name, vcl))
        return self.vcl_list()[name]

    def vcl_list(self):
        vcllist = self.request('vcl.list').splitlines()
        vcls = [Configuration(self, *itm.split()) for itm in vcllist]
        return dict((s.name, s) for s in vcls)

    def _discard_unused_once(self):
        config_still_active = 0
        for config in self.vcl_list().values():
            if config.status == 'active':
                continue

            if config.count > 0:
                print " > '%s' is in use. leaving." % config.name
                config_still_active += 1
                continue

            print " > '%s' is not in use. discarding." % config.name
            config.discard()

        return config_still_active

    def discard_unused(self, attempts=5):
        print "Looking at old configurations to discard"
        for i in range(5):
            if not self._discard_unused_once():
                break
            time.sleep(1)
        else:
            return False
        return True

    def graceful(self, vcl):
        print "Preparing to apply changes from '%s'" % vcl

        conf = self.load(vcl)

        if conf.status != 'active':
            print "Activating configuration changes"
            conf.use()
        else:
            print "Configuration changes already active"

    def test(self, vcl):
        config = self.load(vcl)
        if config.status != 'active':
            config.discard()
        return True

def run(name, telnet, vcl):
    if len(sys.argv) != 2:
        print >>sys.stderr, "Wrong number of arguments"
        sys.exit(1)
    if not sys.argv[1] in ("graceful","configtest"):
        print >>sys.stderr, "(graceful|configtest)"
        sys.exit(1)

    try:
        v = VarnishConnection(*telnet.split(":"))

        if sys.argv[1] == "graceful":
            v.graceful(vcl)
            v.discard_unused()

        elif sys.argv[1] == "configtest":
            v.test(vcl)
            print "Configuration looks ok"

    except VarnishError, e:
        print >>sys.stderr, str(e)
        sys.exit(1)

