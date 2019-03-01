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

py3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
import vim_xactly_connect as vxc
EOF

nnoremap gx gx

function! s:get_visual_selection()
    " Why is this not a built-in Vim script function?!
    let [line_start, column_start] = getpos("'<")[1:2]
    let [line_end, column_end] = getpos("'>")[1:2]
    let lines = getline(line_start, line_end)
    if len(lines) == 0
        return ''
    endif
    let lines[-1] = lines[-1][: column_end - (&selection == 'inclusive' ? 1 : 2)]
    let lines[0] = lines[0][column_start - 1:]
    return join(lines, "\n")
endfunction

nnoremap gxc :VxcConnect 
command! -nargs=1 VxcConnect call VxcConnect(<q-args>)
function! VxcConnect(cust)
	py3 conn=vxc.connection(vim.eval('a:cust'))
endfunction

nnoremap <silent> gxp :VxcObjectExplode <cword><CR>
command! -nargs=1 VxcObjectExplode call VxcObjectExplode(<q-args>)
function! VxcObjectExplode(obj)
	py3 conn.object_explode(vim.eval('a:obj'))
endfunction

nnoremap <silent> gx/ :VxcObjectReverseSearch <cword><CR>
command! -nargs=1 VxcObjectReverseSearch call VxcObjectReverseSearch(<q-args>)
function! VxcObjectReverseSearch(obj)
	py3 conn.object_reverse_search(vim.eval('a:obj'))
endfunction

nnoremap <silent> gxe :VxcExecuteExport <c-r>=getline('.')<CR><CR>
vnoremap <silent> gxe :VxcExecuteExport <c-r>=get_visual_selection()<CR><CR>
command! -nargs=1 VxcExecuteExport call VxcExecuteExport(<q-args>)
function! VxcExecuteExport(cmd)
	py3 conn.execute(vim.eval('a:cmd'))
	py3 conn.result_write()
endfunction

nnoremap <silent> gxx :VxcExecuteSilent <c-r>=getline('.')<CR><CR>
vnoremap <silent> gxx :VxcExecuteSilent <c-r>=get_visual_selection()<CR><CR>
command! -nargs=1 VxcExecuteSilent call VxcExecuteSilent(<q-args>)
function! VxcExecuteSilent(cmd)
	py3 conn.execute(vim.eval('a:cmd'))
endfunction

nnoremap <silent> gxg :VxcObjectExplodeFormat<CR>
command! -nargs=0 VxcObjectExplodeFormat call VxcObjectExplodeFormat()
function! VxcObjectExplodeFormat()
	for i in range(1,10)
		silent! exec 'g/|\s*' . i . '\s*|/' . repeat('>', i)
	endfor
	normal! gg
endfunction

"TODO: make these in python
nnoremap <silent> gxk :VxcGetConnectDefinition <cword><CR>
command! -nargs=1 VxcGetConnectDefinition call VxcGetConnectDefinition(<q-args>)
function! VxcGetConnectDefinition(obj)
	if ("".vim.eval('a:obj') =~ '^s_')
		py3 conn.execute("select command from (show step ". vim.eval('a:obj') . ");")
	elseif ("".vim.eval('a:obj') =~ '^p_')
		py3 conn.execute("select name, position, object_type, object_name, condition, abort_on_condition_false, object_id from (show pipeline ". vim.eval('a:obj') . " members);")
	elseif ("".vim.eval('a:obj') =~ '^v_')
		py3 conn.execute("eval :". vim.eval('a:obj') . ";")
	endif
	py3 conn.result_write()
endfunction

vnoremap <silent> gxk :VxcGetConnectDefinitionVisual <c-r>=getline('.')<CR><CR>
command! -nargs=1 VxcGetConnectDefinitionVisual call VxcGetConnectDefinitionVisual(<q-args>)
function! VxcGetConnectDefinitionVisual(obj)
	if ("".vim.eval('a:obj') =~ '\v^[^. ]+\.[^. ]+')
		py3 conn.execute("select * from ". vim.eval('a:obj') . ";")
	else
		py3 conn.execute("eval ". vim.eval('a:obj') . ";")
	endif
	py3 conn.result_write()
endfunction
