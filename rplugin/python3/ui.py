import pynvim
from io import TextIOWrapper, BytesIO
from contextlib import redirect_stdout
from tqdm import tqdm
import time, sys, re, os, inspect
from functools import reduce

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)
import vim_xactly_connect as vxc

class WriteBuf(TextIOWrapper):
    def __init__(self, buf, index=-1, insert=False, lineoverwrite=True):
        self.buf = buf
        self.index = index if index >= 0 else len(self.buf) + index
        self.insert = insert
        self.lineoverwrite = lineoverwrite
        super().__init__(BytesIO(b'Do not read'))

    def write(self, string):
        lines = list(string.split("\n"))
        for i, l in enumerate(lines):
            if i > 0:
                self.index += 1
            if l != '':
                if self.insert:
                    self._insert_line(l)
                else:
                    self._write_line(l)

    def _write_line(self, line):
        while self.index >= len(self.buf):
            self.buf.append('')
        match = re.match(r'^\r(.*)$', line)
        if match:
            self.buf[self.index] = match.group(1)
        elif self.lineoverwrite:
            self.buf[self.index] = line
        else:
            self.buf[self.index] += line

    def _insert_line(self, line):
        while self.index >= len(self.buf):
            self.buf.append('')
        self.buf.append(line, self.index)

    def readable(self):
        return False

@pynvim.plugin
class VxcPlugin(object):

    def __init__(self, nvim):
        self.nvim = nvim
        self.buf = None

    @pynvim.command('VxcTest', nargs='0', range='', sync=False)
    def vxc_test(self, args, range):
        if self.buf is None:
            self.nvim.command('enew')
            self.nvim.command('setlocal bt=nofile noswf')
            self.nvim.command('file __vxc__')
            self.bufnr = self.nvim.eval('bufnr(\'%\')')
            self.buf = self.nvim.buffers[self.bufnr]

    @pynvim.command('VxcConnect', nargs='1', range='', sync=False)
    def vxc_connect(self, args, range):
        buf = self.nvim.current.buffer
        with WriteBuf(buf) as wbuf, redirect_stdout(wbuf):
            self.conn = vxc.connection(args[0])

    @pynvim.command('VxcSearch', nargs='1', range='', sync=True)
    def vxc_search(self, args, range):
        result = self.conn.object_search(args[0])
        names = reduce(lambda a, b: a + "\n" + b, list(map(lambda x: "\r" + x['name'], result)))
        buf = self.nvim.current.buffer
        buf[:] = []
        with WriteBuf(buf) as wbuf, redirect_stdout(wbuf):
            print(names)

    @pynvim.command('VxcReverseSearch', nargs='0', range='', sync=True)
    def vxc_reverse_search(self, args, range):
        name = self._current_word()
        result = self.conn.object_reverse_search(name)
        names = reduce(lambda a, b: a + "\n" + b, list(map(lambda x: "\r" + x['name'], result)))
        buf = self.nvim.current.buffer
        buf[:] = []
        with WriteBuf(buf) as wbuf, redirect_stdout(wbuf):
            print(names)

    @pynvim.command('VxcShowAll', nargs='0', range='', sync=True)
    def vxc_showall(self, args, range):
        result = self.conn.object_search()
        names = reduce(lambda a, b: a + "\n" + b, list(map(lambda x: x['name'], result)))
        buf = self.nvim.current.buffer
        buf[:] = []
        with WriteBuf(buf) as wbuf, redirect_stdout(wbuf):
            print(names)

    @pynvim.command('VxcDescribe', nargs='0', range='', sync=True)
    def vxc_describe(self, args, range):
        name = self._current_word()
        index = self.nvim.eval('line(".")')
        ret = self.vxc_describe_helper(name)
        buf = self.nvim.current.buffer
        with WriteBuf(buf,index=index,insert=True) as wbuf, redirect_stdout(wbuf):
            if len(ret) > 1:
                for name in ret[1:]:
                    print(name)

    @pynvim.command('VxcEdit', nargs='0', range='', sync=True)
    def vxc_edit(self, args, range):
        name = self._current_word()
        result = self.conn.object_search(name=name)
        if len(result) > 0 and 'command' in result[0]:
            buf = self.nvim.current.buffer
            buf[:] = []
            with WriteBuf(buf) as wbuf, redirect_stdout(wbuf):
                print(result[0]['command'])

        # list support
        # if not isinstance(name, list):
        #     name = [name] if name is not None else []
        # if not isinstance(ID, list):
        #     ID = [ID] if ID is not None else []
        
        # if len(name) > 0:
        #     ID = [self.object_name2id(n) for n in name]
        # if len(ID) > 0:
        #     for i in ID:
        #         ret.extend(self.object_describe_helper(i))

    def vxc_describe_helper(self, name=None, ID=None):
        ret = []
        result = []
        if name is not None:
            result = self.conn.object_search(name=name)
        if ID is not None:
            result = self.conn.object_search(ID=ID)
        if result is not None and len(result) > 0:
            for r in result:
                ret.append(r['name'])
                if 'contains' in r:
                    for i in r['contains']:
                        ret.extend(list(map( lambda a: "  " + a, self.vxc_describe_helper(ID=i) )))
        return ret

    def _current_word(self):
        return self.nvim.eval('expand("<cword>")')
# }}}
