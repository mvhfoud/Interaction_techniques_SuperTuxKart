from oscpy.server import OSCThreadServer
from time import sleep

def dump(address, *values):
    print(u'{}: {}'.format(
        address.decode('utf8'),
        ', '.join(
            '{}'.format(
                v.decode(options.encoding or 'utf8')
                if isinstance(v, bytes)
                else v
            )
            for v in values if values
        )
    ))


def callback(*values):
    print("got values: {}".format(values))

osc = OSCThreadServer(default_handler=dump)  # See sources for all the arguments

# You can also use an \*nix socket path here
sock = osc.listen(address='0.0.0.0', port=8000, default=True)

# osc.bind(b'/multisense/pad/x', callback)

sleep(1000)
osc.stop()  # Stop the default socket