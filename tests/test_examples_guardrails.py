import importlib.util,json,os,subprocess,sys,shutil
from pathlib import Path
from unittest.mock import patch
import pytest
from twylt.guardrails import WorkspaceDenied

ROOT=Path(__file__).resolve().parents[1]

def example(name):
    path=ROOT/'examples'/name/'tool.py'
    spec=importlib.util.spec_from_file_location('example_'+name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def workspace(tmp_path,monkeypatch):
    root=tmp_path/'workspace';root.mkdir()
    monkeypatch.setenv('TWYLT_GUARDRAILS','1')
    monkeypatch.setenv('TWYLT_WORKSPACE_ROOT',str(root))
    monkeypatch.setenv('TWYLT_DISABLE_NETWORK','0')
    monkeypatch.delenv('TWYLT_INCIDENT_LOG',raising=False)
    return root

def test_list_virtual_paths(workspace):
    module=example('list_directory')
    sub=workspace/'sub';sub.mkdir();(sub/'a.txt').write_text('a')
    result=module.TOOL().biz(module.Input(path='/sub'))
    assert [(entry.name,entry.is_dir) for entry in result.entries]==[('a.txt',False)]

@pytest.mark.parametrize('value',['../outside','sub/../../outside'])
def test_list_path_escape(workspace,value):
    module=example('list_directory')
    with pytest.raises(WorkspaceDenied):module.TOOL().biz(module.Input(path=value))

def test_list_checks_requested_link(workspace,tmp_path):
    outside=tmp_path/'outside';outside.mkdir()
    (workspace/'link').symlink_to(outside,target_is_directory=True)
    module=example('list_directory')
    with pytest.raises(WorkspaceDenied):module.TOOL().biz(module.Input(path='link'))

def test_list_checks_child_before_following_link(workspace,tmp_path):
    outside=tmp_path/'outside';outside.mkdir()
    (workspace/'link').symlink_to(outside,target_is_directory=True)
    module=example('list_directory')
    with patch.object(Path,'is_dir',side_effect=AssertionError('must not follow link')):
        with pytest.raises(WorkspaceDenied):module.TOOL().biz(module.Input(path='/'))

def test_ping_network_denied_before_executable_lookup(workspace,monkeypatch):
    module=example('ping');monkeypatch.setenv('TWYLT_DISABLE_NETWORK','1')
    with patch.object(module.shutil,'which',side_effect=AssertionError('must not look up executable')):
        with pytest.raises(WorkspaceDenied):module.TOOL().biz(module.PingInput(host='127.0.0.1'))

def test_ping_safe_invocation(workspace):
    module=example('ping')
    completed=subprocess.CompletedProcess([],0,b'reachable',b'')
    with patch.object(module.shutil,'which',return_value='/usr/bin/ping'),patch.object(module.platform,'system',return_value='Linux'),patch.object(module.subprocess,'run',return_value=completed) as run:
        result=module.TOOL().biz(module.PingInput(host='127.0.0.1',count=1))
    assert result.reachable and not result.timed_out
    assert run.call_args.args[0]==['/usr/bin/ping','-n','-c','1','-W','1','127.0.0.1']
    assert run.call_args.kwargs['stdin'] is subprocess.DEVNULL
    assert not run.call_args.kwargs.get('shell',False)

def test_ping_timeout_and_argument_injection(workspace):
    module=example('ping')
    with patch.object(module.shutil,'which',return_value='/usr/bin/ping'),patch.object(module.platform,'system',return_value='Linux'),patch.object(module.subprocess,'run',side_effect=subprocess.TimeoutExpired([],1,output=b'partial')):
        result=module.TOOL().biz(module.PingInput(host='127.0.0.1'))
        assert result.timed_out and result.stdout=='partial'
    with pytest.raises(ValueError):module.TOOL().biz(module.PingInput(host='-c'))

@pytest.mark.parametrize('name,payload,expected',[('echo',{'text':'  Привет!\n\t'}, {'text':'  Привет!\n\t'}),('ping',{'describe':'json_spec'},None),('list_directory',{'describe':'json_spec'},None)])
def test_standalone_copies_and_disabled_network(tmp_path,name,payload,expected):
    copied=tmp_path/name;copied.mkdir()
    for filename in ['tool.py','run.py']:shutil.copyfile(ROOT/'examples'/name/filename,copied/filename)
    env={**os.environ,'TWYLT_GUARDRAILS':'1','TWYLT_DISABLE_NETWORK':'1','TWYLT_WORKSPACE_ROOT':''}
    result=subprocess.run([sys.executable,str(copied/'run.py'),json.dumps(payload)],env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    output=json.loads(result.stdout)
    if expected is not None:assert output==expected
    else:assert output['inputSchema'] and output['outputSchema']
