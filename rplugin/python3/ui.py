import pynvim
from io import TextIOWrapper, BytesIO
from contextlib import redirect_stdout
from tqdm import tqdm
import time, sys, re, os, inspect

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)
import vim_xactly_connect as vxc

class WriteBuf(TextIOWrapper):
    def __init__(self, buf):
        self.buf = buf
        super().__init__(BytesIO(b'Do not read'))

    def write(self, string):
        lines = list(string.split("\n"))
        for i, l in enumerate(lines):
            if (l != ''):
                match = re.match(r'^\r(.*)$', l)
                if match:
                    self.buf[-1] = match.group(1)
                else:
                    self.buf.append(l)

    def readable(self):
        return False

@pynvim.plugin
class VxcPlugin(object):

    def __init__(self, nvim):
        self.nvim = nvim

    @pynvim.function('TestFunction', sync=False)
    def testfunction(self, args):
        buf = self.nvim.current.buffer
        with WriteBuf(buf) as wbuf, redirect_stdout(wbuf):
            for i in tqdm(range(0,1000), file=sys.stdout):
                time.sleep(.01)

    @pynvim.function('TestVxcConnect', sync=False)
    def vxc_connect(self, args):
        buf = self.nvim.current.buffer
        with WriteBuf(buf) as wbuf, redirect_stdout(wbuf):
            self.conn = vxc.connection(args[0])

