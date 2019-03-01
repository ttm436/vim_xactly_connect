"vxc versions
nnoremap gx gx
nnoremap gxo :call VxcStartup("")<left><left>
nnoremap gxc :call VxcConnect("")<left><left>
nnoremap <silent> gxw :split ~/.vxc/vxc_out<CR>
nnoremap <silent> gxs :split ~/.vxc/settings.json<CR>
nnoremap <silent> gxp "ryiw:call VxcObjectDescribe()<CR>
nnoremap <silent> gx/ "ryiw:call VxcObjectReverseSearch()<CR>
nnoremap <silent> gxe "ryy:call VxcExecuteExport()<CR>
nnoremap <silent> gxx "ryy:call VxcExecuteSilent()<CR>
nnoremap <silent> gxq :call Send_to_Tmux("exit()\n")<CR>
nnoremap <silent> gx; :call Send_to_Tmux("\n")<CR>

vnoremap <silent> gxe "ry:call VxcExecuteExport()<CR>
vnoremap <silent> gxx "ry:call VxcExecuteSilent()<CR>

function! VxcStartup(cust)
	call Send_to_Tmux("cd ~/projects/_personal/vxc/python/;python\n")
	call Send_to_Tmux("import vim_xactly_connect as vxc\n")
	call VxcConnect(a:cust)
endfunction
function! VxcConnect(cust)
	call Send_to_Tmux("conn = vxc.connection(\"". a:cust ."\")\n")
endfunction
function! VxcObjectDescribe()
	call Send_to_Tmux( "conn.object_describe(\"". @r ."\")\n")
endfunction
function! VxcObjectReverseSearch()
	call Send_to_Tmux( "conn.object_reverse_search(\"". @r ."\")\n")
endfunction
function! VxcExecuteExport()
	call Send_to_Tmux("command=\"\"\"\n" . @r . "\n\"\"\"\nconn.execute(command)\nconn.result_write()\n")
endfunction
function! VxcExecuteSilent()
	call Send_to_Tmux("command=\"\"\"\n" . @r . "\n\"\"\"\nconn.execute(command)\n")
endfunction
nnoremap <silent> gxg :call VxcObjectDescribeFormat()<CR>
function! VxcObjectDescribeFormat()
	for i in range(1,10)
		silent! exec 'g/|\s*' . i . '\s*|/' . repeat('>', i)
	endfor
	:call ColorAndAlign()
	:RainbowNoDelim
endfunction
nnoremap <silent> gxk :call VxcGetConnectDefinition(expand('<cword>'))<CR>
function! VxcGetConnectDefinition(obj)
	if (a:obj == 'command')
		let obj=substitute(getline('.'),'\v^(.{-}\|){4}\s*([a-zA-Z0-9_]+).*$', '\2', '')
		call Send_to_Tmux("conn.execute('select command as " . l:obj . " from (show step " . l:obj . ");')\n")
		call Send_to_Tmux("conn.result_write()\n")
	elseif (a:obj =~ '^s_')
		call Send_to_Tmux("conn.execute('select command as " . a:obj . " from (show step " . a:obj . ");')\n")
		call Send_to_Tmux("conn.result_write()\n")
	elseif (a:obj =~ '^v_')
		call Send_to_Tmux("conn.execute('eval :" . a:obj . "')\n")
		call Send_to_Tmux("conn.result_print()\n")
	else
		call Send_to_Tmux("conn.object_describe(name='" . a:obj . "')\n")
	endif
endfunction
vnoremap <silent> gxk "ry:call VxcGetConnectDefinitionVisual()<CR>
function! VxcGetConnectDefinitionVisual()
	if ("".@r =~ '\v^[^. ]+\.[^. ]+')
		call Send_to_Tmux("conn.execute(\"select * from ". @r . ";\")\n")
	else
		call Send_to_Tmux("conn.execute(\"eval ". @r . ";\")\n")
	endif
	call Send_to_Tmux("conn.result_write()\n")
endfunction
 
function! GetVisualSelection()
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

augroup vxc
	autocmd!
	autocmd BufRead vxc_out* syn match VxcPipeline '\v\s*\S+(\s*\|.{-}\|\s*pipeline)@='
	autocmd BufRead vxc_out* hi VxcPipeline ctermfg=15
	autocmd BufRead vxc_out* syn match VxcStep '\v\s*\S+(\s*\|.{-}\|\s*step)@='
	autocmd BufRead vxc_out* hi VxcStep ctermfg=39
	autocmd BufRead vxc_out* syn match VxcVariable '\v\s*\S+(\s*\|.{-}\|\s*variable)@='
	autocmd BufRead vxc_out* hi VxcVariable ctermfg=135
	autocmd BufRead vxc_out* syn match VxcIterator '\v\s*\S+(\s*\|.{-}\|\s*iterator)@='
	autocmd BufRead vxc_out* hi VxcIterator ctermfg=166
	autocmd BufRead vxc_out* syn match VxcEmail '\v\s*\S+(\s*\|.{-}\|\s*email)@='
	autocmd BufRead vxc_out* hi VxcEmail ctermfg=11
	autocmd BufRead vxc_out* setlocal foldmethod=expr
	autocmd BufRead vxc_out* setlocal foldexpr=VxcFoldLevel(v:lnum)
	autocmd BufRead vxc_out* setlocal foldtext=VxcFoldText(v:foldstart)
augroup END

function! VxcFoldLevel(line)
	let cur=matchstr(getline(a:line),'\v(\|\s*)@<=\d+(\s*\|)@=')
	let next=matchstr(getline(a:line+1),'\v(\|\s*)@<=\d+(\s*\|)@=')
	if l:cur < l:next
		return '>' . l:next
	else
		return l:cur
	endif
endfunction

function! VxcFoldText(line)
	let line=getline(a:line)
	return substitute(l:line, '\t', '    ', 'g')
endfunction

