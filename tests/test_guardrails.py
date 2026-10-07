import io,json,os,subprocess,sys
from pathlib import Path
import pytest
from twylt import Tool, ContractModel
from twylt.guardrails import Policy,Workspace,WorkspaceDenied,GuardrailsConfigError,check_network

class Input(ContractModel):
    text: str
class Echo(Tool):
    name='test_echo'
    input_model=output_model=Input
    def biz(self,data): return data

@pytest.fixture
def paths(tmp_path,monkeypatch):
    for key in ['TWYLT_GUARDRAILS','TWYLT_WORKSPACE_ROOT','TWYLT_ALLOWED_CWD','TWYLT_DISABLE_NETWORK','TWYLT_INCIDENT_LOG','INPUT_DESCRIBE']:
        monkeypatch.delenv(key,raising=False)
    ws=tmp_path/'workspace';ws.mkdir()
    runs=tmp_path/'runs';runs.mkdir()
    sub=runs/'a'/'b';sub.mkdir(parents=True)
    monkeypatch.setenv('TWYLT_GUARDRAILS','1');monkeypatch.setenv('TWYLT_WORKSPACE_ROOT',str(ws));monkeypatch.setenv('TWYLT_ALLOWED_CWD',str(runs))
    monkeypatch.chdir(sub);monkeypatch.setattr(sys,'argv',['tool.py']);monkeypatch.setattr(sys,'stdin',io.StringIO(''))
    return ws,runs,sub

def test_nested_cwd_file_transport(paths):
    ws,runs,cwd=paths
    (cwd/'input.json').write_text('{"text":"ok"}')
    Echo.run()
    assert json.loads((cwd/'output.json').read_text())=={'text':'ok'}
    assert Echo.input_path==Path('input.json') and Echo.output_path==Path('output.json')

def test_cwd_does_not_extend_business_workspace(paths):
    ws,runs,cwd=paths
    assert Workspace().resolve('file')==ws/'file'
    with pytest.raises(WorkspaceDenied): Workspace().inspect(cwd/'input.json')
    with pytest.raises(WorkspaceDenied): Workspace().resolve('../runs/file')

@pytest.mark.parametrize('kind',['sibling','symlink_input','symlink_output','absolute_input'])
def test_deny_before_output_removal(paths,monkeypatch,kind):
    ws,runs,cwd=paths
    output=cwd/'output.json';output.write_text('previous')
    (cwd/'input.json').write_text('{"text":"ok"}')
    if kind=='sibling':
        outside=runs.parent/'runs-other';outside.mkdir();monkeypatch.chdir(outside)
        output=outside/'output.json';output.write_text('previous')
    elif kind=='symlink_input':
        (cwd/'input.json').unlink();(cwd/'input.json').symlink_to(ws/'input.json')
    elif kind=='symlink_output':
        target=ws/'previous';target.write_text('previous');output.unlink();output.symlink_to(target)
    else: monkeypatch.setattr(Echo,'input_path',ws/'other.json')
    with pytest.raises(SystemExit) as err: Echo.run()
    assert err.value.code==6
    assert output.read_text()=='previous'

def test_symlink_cwd_root(paths,monkeypatch):
    ws,runs,cwd=paths
    link=runs.parent/'link';link.symlink_to(runs,target_is_directory=True)
    monkeypatch.setenv('TWYLT_ALLOWED_CWD',str(link))
    with pytest.raises(WorkspaceDenied): Policy().transport_path('input.json')

def test_invalid_config(paths,monkeypatch):
    monkeypatch.setenv('TWYLT_GUARDRAILS','maybe')
    with pytest.raises(GuardrailsConfigError): Policy()

def test_network_and_disabled_policy(paths,monkeypatch):
    monkeypatch.setenv('TWYLT_DISABLE_NETWORK','1')
    with pytest.raises(WorkspaceDenied): check_network()
    monkeypatch.setenv('TWYLT_GUARDRAILS','0')
    check_network()
    assert Policy().transport_path('/arbitrary/output.json')==Path('/arbitrary/output.json')
    assert Workspace().resolve('../other')==paths[0]/'../other'

def test_describe_without_configuration(paths,monkeypatch,capsys):
    monkeypatch.delenv('TWYLT_WORKSPACE_ROOT');monkeypatch.delenv('TWYLT_ALLOWED_CWD')
    monkeypatch.setenv('TWYLT_GUARDRAILS','bad');monkeypatch.setattr(sys,'argv',['tool.py','{"describe":"json_spec"}'])
    Echo.run();assert json.loads(capsys.readouterr().out)['name']=='test_echo'

def test_cli_without_workspace(paths,monkeypatch,capsys):
    monkeypatch.delenv('TWYLT_WORKSPACE_ROOT');monkeypatch.delenv('TWYLT_ALLOWED_CWD')
    monkeypatch.setattr(sys,'argv',['tool.py','{"text":"ok"}'])
    Echo.run();assert json.loads(capsys.readouterr().out)=={'text':'ok'}

def test_network_incident_sink_without_workspace(paths,monkeypatch):
    monkeypatch.delenv('TWYLT_WORKSPACE_ROOT');log=paths[1].parent/'audit.jsonl'
    monkeypatch.setenv('TWYLT_INCIDENT_LOG',str(log));monkeypatch.setenv('TWYLT_DISABLE_NETWORK','1')
    with pytest.raises(WorkspaceDenied): check_network('ping')
    event=json.loads(log.read_text());assert event['code']=='network_disabled' and event['tool']=='ping'

@pytest.mark.parametrize('transport',['cli','stdin','env'])
def test_bootstrap_missing_import_describe(paths,transport):
    p=paths[2]/'broken.py';p.write_text('import missing_optional_dependency_xyz\nclass MyTool:\n    name="missing"\n    version="1.0.0"\n    requirements={"tool":"pip","format":"requirements.txt","content":"optional"}\n')
    code='from twylt.bootstrap import run_tool_file;run_tool_file('+repr(str(p))+')'
    args=[sys.executable,'-c',code];env=dict(os.environ);payload='{"describe":"json_spec"}'
    if transport=='cli': args.append(payload)
    if transport=='env': env['INPUT_DESCRIBE']='json_spec'
    r=subprocess.run(args,input=payload if transport=='stdin' else '',capture_output=True,text=True,env=env)
    assert r.returncode==0,r.stderr
    spec=json.loads(r.stdout);assert spec['name']=='missing' and spec['inputSchema']=={}
