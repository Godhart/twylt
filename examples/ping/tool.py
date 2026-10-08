from twylt import Tool, Requirements, ContractModel
import os
import platform
import re
import shutil
import subprocess
import time
from typing import Literal
from pydantic import Field
from twylt.guardrails import check_network


class PingInput(ContractModel):
    host: str = Field(min_length=1,max_length=253,description='Hostname or IP address; no command-line arguments.')
    count: int = Field(default=4,ge=1,le=100,description='Number of ICMP echo requests.')
    timeout: float = Field(default=10,gt=0,le=300,description='Whole process deadline, seconds.')
    family: Literal['auto','ipv4','ipv6'] = Field(default='auto',description='IP address family.')

class PingOutput(ContractModel):
    reachable: bool
    timed_out: bool
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float

def ping(data):
    check_network('ping')
    if data.host.startswith('-') or not re.fullmatch(r'[A-Za-z0-9_.:%-]+',data.host):
        raise ValueError('Invalid host')
    executable = shutil.which('ping')
    if not executable: raise RuntimeError('ping executable is missing; install iputils-ping (Linux)')
    family = [] if data.family == 'auto' else ['-4' if data.family == 'ipv4' else '-6']
    system = platform.system()
    if system == 'Windows': args = [executable,*family,'-n',str(data.count),'-w','1000',data.host]
    elif system == 'Linux': args = [executable,*family,'-n','-c',str(data.count),'-W','1',data.host]
    else: raise RuntimeError('ping currently supports Linux and Windows')
    start = time.monotonic()
    try:
        result = subprocess.run(args,capture_output=True,timeout=data.timeout,check=False,env={**os.environ,'LC_ALL':'C'},stdin=subprocess.DEVNULL)
        return PingOutput(reachable=result.returncode==0,timed_out=False,returncode=result.returncode,stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace'),elapsed_seconds=time.monotonic()-start)
    except subprocess.TimeoutExpired as exc:
        return PingOutput(reachable=False,timed_out=True,returncode=None,stdout=(exc.stdout or b'').decode(errors='replace'),stderr=(exc.stderr or b'').decode(errors='replace'),elapsed_seconds=time.monotonic()-start)

class Ping(Tool[PingInput, PingOutput]):
    input_model = PingInput
    output_model = PingOutput
    name = 'ping'
    version = '1.0.0'
    description = 'Check ICMP reachability using the operating system ping utility.'
    requirements = Requirements(tool='pip', format='requirements.txt', content='twylt>=1.1.0,<2\npydantic>=2,<3\n')
    few_shots = [{'input': {'host': '127.0.0.1', 'count': 1}, 'output': {'reachable': True, 'timed_out': False, 'returncode': 0, 'stdout': '', 'stderr': '', 'elapsed_seconds': 0.01}}]
    input_schema_name = 'ping.input'
    input_schema_version = '1.0.0'
    output_schema_name = 'ping.output'
    output_schema_version = '1.0.0'
    def biz(self, data):
        return ping(data)

TOOL = Ping
if __name__ == '__main__':
    Ping.run()
