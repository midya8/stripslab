"""UTF-8 JSON CLI. Output replacement occurs only after successful validation."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import audit


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description='Exact bounded unit-cost positive STRIPS witnesses')
    p.add_argument('input',help='JSON path or - for stdin')
    p.add_argument('-o','--output',help='output JSON path; default stdout')
    args=p.parse_args(argv)
    try:
        raw=sys.stdin.buffer.read(65537) if args.input=='-' else Path(args.input).read_bytes()
        if len(raw)>65536:
            raise ValueError('input exceeds 65536 UTF-8 bytes')
        data=json.loads(raw.decode('utf-8'),object_pairs_hook=unique_object,
                        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON constant')))
        result=audit(data)
        text=json.dumps(result,ensure_ascii=True,allow_nan=False,indent=2)+'\n'
        if args.output:
            target=Path(args.output)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,delete=False) as f:
                tmp=f.name
                try:f.write(text)
                except BaseException:
                    os.unlink(tmp)
                    raise
            try:os.replace(tmp,target)
            except BaseException:
                os.unlink(tmp)
                raise
        else:sys.stdout.write(text)
    except (ValueError,OSError,UnicodeError,RecursionError) as e:
        p.exit(2,'Invalid input: '+str(e)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
