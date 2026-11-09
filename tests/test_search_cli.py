import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from stripslab.search import audit_search
ROOT=Path(__file__).resolve().parents[1]
class SearchCLITests(unittest.TestCase):
 def test_search_flag_stdin_file_and_atomic_rejection(self):
  x=json.loads((ROOT/'docs/search-controls.json').read_text())[0]['input'];expected=audit_search(x)
  p=subprocess.run([sys.executable,'-m','stripslab','--search','-'],input=json.dumps(x),text=True,capture_output=True,check=True);self.assertEqual(json.loads(p.stdout),expected)
  with tempfile.TemporaryDirectory() as d:
   source=Path(d)/'in.json';out=Path(d)/'out.json';source.write_text(json.dumps(x));subprocess.run([sys.executable,'-m','stripslab','--search',str(source),'-o',str(out)],check=True);self.assertEqual(json.loads(out.read_text()),expected);old=out.read_bytes()
   for invalid in [b'{}',b'{"facts":1,"facts":2}',b'\xff',b'x'*65537]:
    source.write_bytes(invalid);p=subprocess.run([sys.executable,'-m','stripslab','--search',str(source),'-o',str(out)],capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(out.read_bytes(),old)
