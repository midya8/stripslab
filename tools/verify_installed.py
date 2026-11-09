"""Runs outside the checkout; compare complete reports and both entry points."""
import json,subprocess,sys
from pathlib import Path
import stripslab,stripslab.core,stripslab.__main__
from stripslab import audit
expected=json.loads(Path(sys.argv[1]).read_text())
origins={m.__name__:str(Path(m.__file__).resolve()) for m in [stripslab,stripslab.core,stripslab.__main__]}
assert all('site-packages' in p for p in origins.values()),origins
for case in expected:
 x,r=case['input'],case['report'];assert audit(x)==r
 for command in [[sys.executable,'-m','stripslab'],[str(Path(sys.executable).parent/'stripslab')]]:
  p=subprocess.run(command+['-'],input=json.dumps(x),text=True,capture_output=True,check=True);assert json.loads(p.stdout)==r
print(json.dumps(dict(installed_reports=len(expected),module_origins=origins,CLIs=2)))
