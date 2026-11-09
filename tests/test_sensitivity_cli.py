import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from stripslab.sensitivity import audit_sensitivity
class SensitivityCLI(unittest.TestCase):
 def test_cli_and_atomic_strict_rejections(self):
  task={'facts':1,'initial':[],'goal':[0],'actions':[{'pre':[],'add':[0],'delete':[]}]}
  cmd=[sys.executable,'-m','stripslab','--sensitivity']
  result=subprocess.run(cmd+['-'],input=json.dumps(task),text=True,capture_output=True,check=True)
  self.assertEqual(json.loads(result.stdout),audit_sensitivity(task))
  with tempfile.TemporaryDirectory() as d:
   source=Path(d)/'in.json';out=Path(d)/'out.json';source.write_text(json.dumps(task))
   subprocess.run(cmd+[str(source),'-o',str(out)],check=True)
   self.assertEqual(json.loads(out.read_text()),audit_sensitivity(task))
   for bad in [b'{}',b'{"facts":1,"facts":1}',b'NaN',b'\xff',b' '*65537]:
    out.write_text('preserve');r=subprocess.run(cmd+['-','-o',str(out)],input=bad,capture_output=True)
    self.assertEqual(r.returncode,2);self.assertEqual(out.read_text(),'preserve');self.assertEqual(r.stdout,b'')
  self.assertEqual(subprocess.run(cmd+['--search','-'],input=b'{}',capture_output=True).returncode,2)
