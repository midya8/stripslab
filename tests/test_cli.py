import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from stripslab import audit
class CLI(unittest.TestCase):
 def test_stdout(self):
  d=dict(facts=2,initial=[],goal=[1],actions=[dict(pre=[],add=[1],delete=[])])
  p=subprocess.run([sys.executable,'-m','stripslab','-'],input=json.dumps(d),capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),audit(d))
 def test_atomic_and_strict_json(self):
  with tempfile.TemporaryDirectory() as temp:
   source=Path(temp)/'in.json';out=Path(temp)/'out.json';out.write_text('retain me')
   for text in ['{}','{"facts":1,"initial":[],"goal":[],"actions":[],"facts":2}','{"facts":NaN,"initial":[],"goal":[],"actions":[]}', ' '*65537,'[[[[']:
    source.write_text(text);p=subprocess.run([sys.executable,'-m','stripslab',str(source),'-o',str(out)],capture_output=True,text=True)
    self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),'retain me')
   d=dict(facts=0,initial=[],goal=[],actions=[]);source.write_text(json.dumps(d))
   subprocess.run([sys.executable,'-m','stripslab',str(source),'-o',str(out)],check=True)
   self.assertEqual(json.loads(out.read_text()),audit(d));self.assertEqual(sorted(p.name for p in Path(temp).iterdir()),['in.json','out.json'])
 def test_invalid_utf8(self):
  p=subprocess.run([sys.executable,'-m','stripslab','-'],input=b'\xff',capture_output=True);self.assertEqual(p.returncode,2)
