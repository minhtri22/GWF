from __future__ import annotations
import hashlib, json, sys
from .tabular_verifier import TabularStatistics

def main():
    raw=sys.stdin.buffer.read()
    payload=json.loads(raw)
    result=TabularStatistics.verify(payload)
    result["input_sha256"]=hashlib.sha256(raw).hexdigest()
    sys.stdout.write(json.dumps(result, sort_keys=True))

if __name__ == "__main__": main()
