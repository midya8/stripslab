"""Run outside checkout, compare complete base/search reports and both entry points."""
import json,subprocess,sys
from pathlib import Path
import stripslab,stripslab.core,stripslab.__main__,stripslab.search,stripslab.sensitivity
from stripslab import audit
from stripslab.search import audit_search
from stripslab.sensitivity import audit_sensitivity
expected=json.loads(Path(sys.argv[1]).read_text())
origins={m.__name__:str(Path(m.__file__).resolve()) for m in [stripslab,stripslab.core,stripslab.__main__,stripslab.search,stripslab.sensitivity]}
assert all('site-packages' in p for p in origins.values()),origins
for mode,fn,flags in [('base',audit,[]),('search',audit_search,['--search']),('sensitivity',audit_sensitivity,['--sensitivity'])]:
 for case in expected[mode]:
  x,r=case['input'],case['report'];assert fn(x)==r
  for command in [[sys.executable,'-m','stripslab'],[str(Path(sys.executable).parent/'stripslab')]]:
   p=subprocess.run(command+flags+['-'],input=json.dumps(x),text=True,capture_output=True,check=True);assert json.loads(p.stdout)==r
print(json.dumps(dict(installed_reports={k:len(v) for k,v in expected.items()},module_origins=origins,CLIs=2,modes=3)))
