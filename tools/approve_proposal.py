from __future__ import annotations
import argparse, getpass, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from gwr.runtime import GovernedWorkflowRuntime


def main():
    ap=argparse.ArgumentParser(description='Authenticated human approval CLI')
    ap.add_argument('--db',required=True)
    ap.add_argument('--proposal-id',required=True)
    ap.add_argument('--username',required=True)
    ap.add_argument('--domain',default=str(ROOT/'domains'/'research.workflow.yaml'))
    args=ap.parse_args()
    secret=os.environ.get('GWR_AUTH_SECRET')
    if not secret:
        raise SystemExit('GWR_AUTH_SECRET must be set so the approval session can be verified across processes')
    password=getpass.getpass('Human password: ')
    rt=GovernedWorkflowRuntime(args.domain,args.db,auth_secret=secret)
    row=rt.db.one('SELECT * FROM proposals WHERE proposal_id=?',(args.proposal_id,))
    if not row:
        raise SystemExit('proposal not found')
    print('Action:',row['action'])
    print('Payload hash:',row['payload_hash'])
    print('Frozen payload:',row['frozen_payload'])
    answer=input('Approve this exact payload? [yes/NO] ').strip().lower()
    if answer!='yes':
        raise SystemExit('approval cancelled')
    token=rt.auth.authenticate(args.username,password,client_metadata={'client':'approve_proposal_cli'})
    aid=rt.governance.approve_proposal_authenticated(args.proposal_id,token,row['payload_hash'])
    rt.auth.revoke(token)
    print('Approved:',aid)
    rt.close()

if __name__=='__main__': main()
