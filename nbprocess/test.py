# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/14_test.ipynb.

# %% auto 0
__all__ = ['test_nb', 'nbprocess_test']

# %% ../nbs/14_test.ipynb 2
import time,os,sys,traceback,contextlib

from fastcore.utils import *
from fastcore.script import *
from fastcore.imports import *
from .read import *
from .doclinks import *
from .process import NBProcessor
from logging import warning

# %% ../nbs/14_test.ipynb 4
def _do_eval(cell, flags):
    if cell.cell_type != 'code': return False
    direc = getattr(cell, 'directives_', {}) or {}
    if direc.get('eval:', [''])[0].lower() == 'false': return False
    return not flags & direc.keys()

# %% ../nbs/14_test.ipynb 5
def _format_code(code_list, lineno):
    _fence = '-'*50
    l=[_fence]
    for i,c in enumerate(code_list, start=1):
        if i == lineno: l.append(f"---> {i} {c}")
        else: l.append(f"     {i} {c}")
    l.append(_fence)
    return '\n'.join(l)

# %% ../nbs/14_test.ipynb 7
def _skip_frame(tb): return '/tinykernel/tinykernel/' not in tb.tb_frame.f_back.f_code.co_filename


def test_nb(fn, skip_flags=None, force_flags=None, do_print=False):
    "Execute tests in notebook in `fn` except those with `skip_flags`"
    if not IN_NOTEBOOK: os.environ["IN_TEST"] = '1'
    flags=set(L(skip_flags)) - set(L(force_flags))
    k,start = NBRunner(),time.time()
    
    def _exec_cell(cell):
        try:
            if _do_eval(cell, flags): k.run(cell)
        except Exception as e:
            _fence = '='*75
            tb = e.__traceback__
            while tb and _skip_frame(tb): tb = tb.tb_next
            line_no = tb.tb_next.tb_lineno #changes to the tinykernel library could break this
            warning(f"line no: {line_no}")
            tb_str = '\n'.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)[-2:])
            cell_str = f"\nWhile Executing Cell #{cell.idx_}:\n{_format_code(cell.source.splitlines(), line_no)}"
            warning(f"{type(e).__name__} in {fn}:\n{_fence}\n{cell_str}\n{tb_str}\n") 
            raise Exception('nbprocess test failed')
    try:
        if do_print: print(f'Starting {fn}')
        with open(os.devnull, "w") as f, contextlib.redirect_stdout(f): NBProcessor(fn, _exec_cell).process()
        if do_print: print(f'- Completed {fn}')
        return True,time.time()-start
    except:
        return False,time.time()-start

# %% ../nbs/14_test.ipynb 11
@call_parse
def nbprocess_test(
    fname:str=None,  # A notebook name or glob to convert
    flags:str='',  # Space separated list of test flags you want to run that are normally ignored
    n_workers:int=None,  # Number of workers to use
    timing:bool=False,  # Timing each notebook to see the ones are slow
    do_print:str=False, # Print start and end of each NB
    pause:float=0.01  # Pause time (in secs) between notebooks to avoid race conditions
):
    "Test in parallel the notebooks matching `fname`, passing along `flags`"
    skip_flags = config_key('tst_flags', '', path=False).split()
    force_flags = flags.split()
    files = [Path(f).absolute() for f in sorted(nbglob(fname))]
    if n_workers is None: n_workers = 0 if len(files)==1 else min(num_cpus(), 8)
    os.chdir(config_key("nbs_path"))
    results = parallel(test_nb, files, skip_flags=skip_flags, force_flags=force_flags, n_workers=n_workers, pause=pause, do_print=do_print)
    passed,times = zip(*results)
    if all(passed): print("Success.")
    else: 
        _fence = '='*50
        sys.stderr.write(f"\nnbprocess Tests Failed On The Following Notebooks:\n{_fence}\n\t" + '\n\t'.join([f.name for p,f in zip(passed,files) if not p]))
        exit(1)
    if timing:
        for i,t in sorted(enumerate(times), key=lambda o:o[1], reverse=True): print(f"{files[i].name}: {int(t)} secs")
