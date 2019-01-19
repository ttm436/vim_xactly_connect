let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

if !has("python3")
    echo "vim has to be compiled with +python3 to run this"
    finish
endif

if exists('g:vim_xactly_connect_plugin_loaded')
	echo "already loaded"
    finish
endif

python << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
import vim_xactly_connect
EOF

function! XactlyConnectSetConnection(name)
	python set_connection(name)
endfunction
command! -nargs=1 XCSetConnection call XactlyConnectSetConnection(<q-args>)

function! XactlyConnectExecuteCommand(command)
	python execute_command(command)
endfunction
command! -nargs=1 XCExecuteCommand call XactlyConnectExecuteCommand(<q-args>)

function! XactlyConnectPrintResult()
	python print_result()
endfunction
command! -nargs=0 XCPrintResult call XactlyConnectPrintResult()

let g:vim_xactly_connect_plugin_loaded = 1
