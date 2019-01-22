let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

if !has("python3")
    echo "vim has to be compiled with +python3 to run this"
    finish
endif

if exists('g:vim_xactly_connect_plugin_loaded')
	echo "already loaded"
    finish
endif
let g:vim_xactly_connect_plugin_loaded = 1

python << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
import vim_xactly_connect as vxc
EOF

command! -nargs=1 XCConnectionOpen call XactlyConnectConnectionOpen(<q-args>)
function! XactlyConnectConnectionOpen(name)
	python vxc.connection_open(name)
endfunction

command! -nargs=1 XCConnectionClose call XactlyConnectConnectionClose(<q-args>)
function! XactlyConnectConnectionClose(name)
	python vxc.connection_close(name)
endfunction

command! -nargs=1 XCCommandExecute call XactlyConnectCommandExecute(<q-args>)
function! XactlyConnectCommandExecute(command)
	python vxc.command_execute(command)
endfunction

command! -nargs=0 XCResultPrint call XactlyConnectResultPrint()
function! XactlyConnectResultPrint()
	python vxc.result_print()
endfunction

command! -nargs=0 XCResultWrite call XactlyConnectResultWrite()
function! XactlyConnectResultWrite()
	python vxc.result_write()
endfunction

