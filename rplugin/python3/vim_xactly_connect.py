import os, sys, json, re
from functools import reduce
import jaydebeapi as jdb
from tqdm import tqdm
import objectpath as objp
from datetime import datetime
from contextlib import redirect_stdout

HOME_DIR      = os.path.expanduser('~')
VXC_HOME_DIR  = HOME_DIR + '/.vxc/'
CACHE_DIR     = VXC_HOME_DIR + '/cache/'
SETTINGS_PATH = VXC_HOME_DIR + 'settings.json'
RESULTS_PATH  = VXC_HOME_DIR + 'vxc_out'
DATETIME_PARSE = '%Y-%m-%dT%H:%M:%S.%fZ'
class suppress_stdout_stderr(object):# {{{
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).
    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)
# }}}

class connection(object):

#__init__# {{{

    def __init__(self, name):
        settings = settings_load()
        if len(settings) > 0 and name in settings:
            print("Connecting to " + name + "'s Connect instance ...")
            self.connection_name = name
            self.setting = settings[name]
            try:
                self.conn = jdb.connect(
                    self.setting['driver_class'],
                    self.setting['url'],
                    [self.setting['username'],self.setting['password']],
                    self.setting['path']
                )
            except Exception as e:
                print(e)
                exit()
            print("Connection Success")
            self.curs = self.conn.cursor()
            self.cache_filename = CACHE_DIR + name + '.json'
            self.cache = {}
            if (os.path.exists(self.cache_filename)):
                with open(self.cache_filename) as cache_file:
                    self.cache = json.load(cache_file)
            self.cache_tree = objp.Tree(self.cache)
            self.cache_refresh()
        else:
            print("Connection settings for project \"" + name + "\" not found in " + SETTINGS_PATH)
            exit()

# }}}
#execute# {{{

    def execute(self, command):
        with suppress_stdout_stderr():
            self.curs.execute(command)
            try:
                self.result = self.curs.fetchall()
            except Exception as e:
                self.result = None
                print("No Result")

# }}}
#result_print# {{{

    def result_print(self):
        print(result2string(self.result, self.curs.description))

# }}}
#result_write# {{{

    def result_write(self):
        with open(RESULTS_PATH, 'w') as file_out:
            file_out.write(result2string(self.result, self.curs.description))
        print(str(len(self.result)) + " lines.")

# }}}
#cache_refresh# {{{

    def cache_refresh(self, force=False):
        print("Refreshing Cache ...")
        command = '''
select name, id, modified_instant, 'pipeline' as type from (show pipelines)
union select name, id, modified_instant, 'deploycontainer' as type from (show deploycontainers)
union select name, id, modified_instant, 'step' as type from (show steps)
union select name, id, modified_instant, 'variable' as type from (show variables)
union select name, id, modified_instant, 'email' as type from (show emails)
union select name, id, modified_instant, 'iterator' as type from (show iterators)
'''
        self.execute(command)
        objs_all = self.result
        if (not force):
            objs_mod = list(filter(lambda obj:
                obj[1] not in self.cache
                    or ('modified_instant' not in self.cache[obj[1]])
                    or (obj[2] is not None and self.cache[obj[1]]['modified_instant'] == 'None')
                    or (obj[2] is not None and self.cache[obj[1]]['modified_instant'] != 'None'
                        and to_datetime(obj[2]) > to_datetime(self.cache[obj[1]]['modified_instant']))
                , objs_all
            ))
        else:
            objs_mod = objs_all
                
        print ("Modified Objects : " + str(len(objs_mod)))
        dict_out = self.objects_download(objs_mod)
        dict_out.update({ k : v for k, v in self.cache.items()
            if k in list(map(lambda x: x[1], objs_all))
                and k not in list(map(lambda x: x[1], objs_mod))
        })
        self.cache = dict_out
        self.cache_tree = objp.Tree(self.cache)
        print ("Linking steps ...")
        self.cache_link_steps()
        self.cache_tree = objp.Tree(self.cache)
        print ("Writing cache ...")
        json_write(self.cache, self.cache_filename)
        print ("Done")

# }}}
#objects_download# {{{

    def objects_download(self, objs):
        dict_out = {}
        if len(objs) > 0:
            # {{{ const
            types = {'pipeline':      'select a.name, a.id, a.ContinueOnError, a.OnError, a.Finally, GatherString(b.object_id) as members, a.modified_instant from (show pipeline {0}) as a left join (select name, object_id from (show pipeline {0} members)) as b on a.name = b.name',
                   'step':            'select name, id, command, modified_instant from (show step {})',
                   'deploycontainer': 'select name, id, contentInJson, modified_instant from (show deploycontainers) where name = \'{}\'',
                   'email':           'select name, id, "as", modified_instant from (show email {})',
                   'variable':        'select name, id, value, modified_instant from (show variable {})',
                   'iterator':        'select name, id, object_id, "over", modified_instant from (show iterator {})'
            }
            mapping = {
                'pipeline': (lambda:
                    {x[1]:
                        {
                            'name':             str(x[0]),
                            'id':               str(x[1]),
                            'type':             'pipeline',
                            'ContinueOnError':  str(x[2]),
                            'OnError':          str(x[3]),
                            'Finally':          str(x[4]),
                            'contains':         str(x[5]).split(','),
                            'modified_instant': str(x[6])
                        } for x in self.result
                    }),
                'step': (lambda:
                    {x[1]:
                        {
                            'name':             str(x[0]),
                            'id':               str(x[1]),
                            'type':             'step',
                            'command':          str(x[2]),
                            'modified_instant': str(x[3])
                        } for x in self.result
                    }),
                'deploycontainer': (lambda:
                    {x[1]:
                        {
                            'name':             str(x[0]),
                            'id':               str(x[1]),
                            'type':             'deploycontainer',
                            'contains':         [i for v in json.loads(x[2]).values() for i in v],
                            'modified_instant': str(x[3])
                        } for x in self.result
                    }),
                'email': (lambda:
                    {x[1]:
                        {
                            'name':             str(x[0]),
                            'id':               str(x[1]),
                            'type':             'email',
                            'definition':       str(x[2]),
                            'modified_instant': str(x[3])
                        } for x in self.result
                    }),
                'variable': (lambda:
                    {x[1]:
                        {
                            'name':             str(x[0]),
                            'id':               str(x[1]),
                            'type':             'variable',
                            'value':            str(x[2]),
                            'modified_instant': str(x[3])
                        } for x in self.result
                   }),
                'iterator': (lambda:
                    {x[1]:
                        {
                            'name':             str(x[0]),
                            'id':               str(x[1]),
                            'type':             'iterator',
                            'contains':         str(x[2]),
                            'over':             str(x[3]),
                            'modified_instant': str(x[4])
                        } for x in self.result
                    })
            }
# }}}
            cmd = {}
            for t in types:
                cmd.update({t:''})
            for obj in objs:
                obj_name = obj[0]
                obj_type = obj[3]
                for t, c in types.items():
                    if obj_type == t:
                        if cmd[t] != '':
                            cmd[t] += ' union '
                        cmd[t] += c.format(obj_name)
            print("Downloading Objects ...")
            for t in tqdm(types, file=sys.stdout):
                if cmd[t] != '':
                    cmd[t] += ';'
                    self.execute(cmd[t])
                    dict_out.update(mapping[t]())
        return dict_out

# }}}
# cache_link_steps{{{

    def cache_link_steps(self):
        steps = list(self.cache_tree.execute("$..*[@.type is 'step']"))
        re_strs = [
            # invoked objects
            'invoke\s*\S+\s*([a-zA-Z0-9_]+)',
            # set variables
            'set\s*([a-zA-Z0-9_]+)\s*\*=',
            # referenced variables
            ':([a-zA-Z0-9_]+)'
        ]
        for v in steps:
            contains = []
            cmd = v['command']
            # invoked pipeline/step/iterator
            for re_str in re_strs:
                for match in re.finditer(re_str, cmd):
                    ID = self.object_name2id(match.group(1)) 
                    if ID not in contains:
                        contains.append(ID)
            v.update({'contains' : contains})
            self.cache[v['id']] = v

# }}}
#object_describe# {{{

    def object_describe(self, name=None, ID=None):
        ret = []
        if not isinstance(name, list):
            name = [name] if name is not None else []
        if not isinstance(ID, list):
            ID = [ID] if ID is not None else []

        if len(name) > 0:
            ID = [self.object_name2id(n) for n in name]
        if len(ID) > 0:
            for i in ID:
                ret.extend(self.object_describe_helper(i))

        with open( RESULTS_PATH, 'w') as file_out:
            #result string takes list of lists (or tuples)
            desc = (('name',),( 'ID',),( 'type',),( 'depth',),( 'contained_by_name',),( 'contained_by_id',))
            file_out.write(result2string(ret, desc))

# }}}
#object_describe_helper# {{{

    def object_describe_helper(self, ID=None):
        ret_list = []
        cur_dict = {}
        if ID is not None and ID in self.cache:
            cur_dict = self.cache[ID]
            # name ID type depth contained_by_name contained_by_id
            ret_list = [ (cur_dict['name'], cur_dict['id'], cur_dict['type'], 0, '', '') ]
            if 'command' in cur_dict:
                ret_list.append(('command', '', 'command', 1, cur_dict['name'], cur_dict['id']))
            if 'contains' in cur_dict:
                for next_id in cur_dict['contains']:
                    ret_list.extend( list( map(
                        lambda x: (
                            x[0], x[1], x[2], x[3] + 1,
                            cur_dict['name'] if x[4] == '' else x[4],
                            cur_dict['id'] if x[5] == '' else x[5]
                        ), self.object_describe_helper(next_id)
                    )))
        return ret_list

# }}}
#object_search# {{{

    def object_search(self, search=None, name=None, ID=None, type=None, reverse=False):
        cmd = ''
        if name is not None:
            ID = self.object_name2id(name)
        if ID is not None:
            if reverse:
                cmd += "'" + ID + "' in @.contains"
            else:
                cmd += "'" + ID + "' in @.id"
        else:
            if search is not None:
                cmd += "'" + search + "' in @.name"
            if type is not None:
                if cmd != '':
                    cmd += ' and '
                cmd += "'" + type + "' in @.type"
        if cmd == '':
            cmd = '1 is 1'
        id_list = list(self.cache_tree.execute("$..*[" + cmd + "].id"))
        self.object_describe(ID=id_list)

# }}}
#object_reverse_search# {{{

    def object_reverse_search(self, name=None, ID=None, type=None):
        self.object_search(None,name,ID,type,True)

# }}}
#object_name2id# {{{

    def object_name2id(self, name):
        lst = list(self.cache_tree.execute("$..*[@.name is '" + name + "']"))
        if lst is not None and len(lst) > 0:
            return lst[0]['id']

# }}}
#object_id2name# {{{

    def object_id2name(self, ID):
        return self.cache[ID]['name']

# }}}

# End class connection

#Util
def to_datetime(string):
    string = str(string)
    if '.' not in string:
        string = string.replace('Z','.0Z')
    return datetime.strptime(string, DATETIME_PARSE)

def result2string(result, description):
    out_str = ''
    if description is not None:
        desc = map(lambda a: str(a[0]), description)
        out_str += reduce(lambda a, b: a + '|' + b, desc) + "\n"
    if result is not None:
        for a in result:
            if len(a) > 1:
                out_str += str(reduce(lambda b, c: str(b) + '|' + str(c), a)) + "\n"
            elif len(a) == 1:
                out_str += str(a[0])
    return out_str
         
def settings_load():
    global settings
    with open(SETTINGS_PATH) as settings_file:
        return json.load(settings_file)

def json_write(obj, file_name):
    string_out = json.dumps(obj, indent = 4)
    with open(file_name, 'w') as file_out:
        file_out.write(string_out)
    return obj

## Directory initialization ##
if not os.path.exists(VXC_HOME_DIR):
    os.mkdir(VXC_HOME_DIR)
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
if not os.path.exists(SETTINGS_PATH):
    sample = {
        "sample" : {
            "driver_class" : "com.xactly.connect.jdbc.Driver",
            "url" : "jdbc:xactly://implement1.xactlycorp.com:443?useSSL=true",
            "username" : "",
            "password" : "",
            "path" : "path/to/xjdbcdriver/xjdbc-with-dependencies-1.2.0-RELEASE.jar"
        }
    }
    json_write(sample, SETTINGS_PATH)

