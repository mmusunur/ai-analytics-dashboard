"""Quick verification that workspace/project fixes work."""
import sys
sys.path.insert(0, 'agents')
sys.path.insert(0, 'scripts')
from dotenv import load_dotenv
load_dotenv()
from plane_agent import list_workspaces, list_projects

ws = list_workspaces()
print('Workspaces:', ws)

projs = list_projects('agentbuilder')
print(f'Projects ({len(projs)}):')
for p in projs:
    ident = p.get('identifier', '?')
    name  = p.get('name', '?')
    pid   = str(p.get('id', '?'))[:8]
    print(f'  [{ident}] {name} | id={pid}')
