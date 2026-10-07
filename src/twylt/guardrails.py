"""TWYLT 1.1.0 opt-in cooperative guardrails.
Explicit path confinement, not an OS sandbox. Environment is trusted configuration.
"""
import contextvars
import datetime as _datetime
import json as _json
import os as _os
from pathlib import Path as _Path
import stat as _stat
import sys as _sys
import uuid as _uuid

_POLICY = contextvars.ContextVar('twylt_workspace', default=None)


def env_bool(name, default=False):
    value = _os.environ.get(name)
    if value is None: return default
    value = value.strip().lower()
    if value in {'1', 'true', 'yes', 'on'}: return True
    if value in {'0', 'false', 'no', 'off'}: return False
    raise GuardrailsConfigError(f'{name}: expected a boolean value')

class GuardrailsConfigError(ValueError):
    pass

class Policy:
    def __init__(self, tool='unknown'):
        self.tool = tool
        self.enabled = env_bool('TWYLT_GUARDRAILS')
        self.disable_network = env_bool('TWYLT_DISABLE_NETWORK')
        self.allowed_cwd = _os.environ.get('TWYLT_ALLOWED_CWD', '')
        if self.enabled and self.allowed_cwd and not _Path(self.allowed_cwd).is_absolute():
            raise GuardrailsConfigError('TWYLT_ALLOWED_CWD must be absolute')

    def check_network(self):
        if self.enabled and self.disable_network:
            Workspace(self.tool, require_root=False).deny('network_disabled')

    def transport_path(self, value):
        path = _Path(value)
        if not self.enabled: return path
        cwd = _Path.cwd()
        roots = [_os.environ.get('TWYLT_WORKSPACE_ROOT', ''), self.allowed_cwd]
        for root in roots:
            if not root: continue
            ws = Workspace(self.tool, root_override=root)
            if ws.contains(cwd):
                ws.inspect(cwd)
                full = _Path(_os.path.abspath(path if path.is_absolute() else cwd/path))
                # Additional cwd roots authorize transport files only in the actual cwd.
                if full.parent != cwd: continue
                return ws.inspect(full)
        Workspace(self.tool, require_root=False).deny('transport_cwd_or_path_outside_allowed_roots')

def check_network(tool='unknown'):
    Policy(tool).check_network()

class WorkspaceDenied(ValueError):
    """A policy denial, already recorded in the incident sink."""
    def __init__(self, code, incident_id):
        self.code = code
        self.incident_id = incident_id
        super().__init__(f'{code}: access denied (incident {incident_id})')

class Workspace:
    def __init__(self, tool='unknown', *, root_override=None, require_root=True):
        self.enabled = env_bool('TWYLT_GUARDRAILS')
        self.tool = tool
        self.log_path = None
        self.root = None
        value = root_override if root_override is not None else _os.environ.get('TWYLT_WORKSPACE_ROOT', '')
        if not self.enabled:
            self.root = _Path(value).absolute() if value else _Path.cwd()
            return
        if not value and not require_root:
            value = None
        if value is not None and (not value or not _Path(value).is_absolute()):
            self.deny('workspace_not_configured')
        if value is not None:
            candidate = _Path(_os.path.abspath(value))
            # The root and all of its ancestors must be real directories.
            try:
                for part in [*reversed(candidate.parents), candidate]:
                    st = part.lstat()
                    if self._link(st) or not _stat.S_ISDIR(st.st_mode):
                        self.deny('invalid_workspace_root')
                if candidate.parent == candidate:
                    self.deny('filesystem_root_forbidden')
            except OSError:
                self.deny('invalid_workspace_root')
            self.root = candidate
        configured_log = _os.environ.get('TWYLT_INCIDENT_LOG', '')
        if configured_log:
            p = _Path(configured_log)
            if not p.is_absolute(): self.deny('invalid_incident_log')
            p = _Path(_os.path.abspath(p))
            if self.contains(p): self.deny('incident_log_inside_workspace')
            try:
                for parent in [*reversed(p.parent.parents), p.parent]:
                    st = parent.lstat()
                    if self._link(st) or not _stat.S_ISDIR(st.st_mode):
                        self.deny('invalid_incident_log')
                self.log_path = p
                fd = self._open_log()
                _os.close(fd)
            except WorkspaceDenied:
                raise
            except (OSError, ValueError):
                self.log_path = None
                self.deny('incident_log_unavailable')

    @staticmethod
    def _link(st):
        # Includes Windows junctions/reparse points even on Python without is_junction().
        return _stat.S_ISLNK(st.st_mode) or bool(getattr(st, 'st_file_attributes', 0) & 0x400)

    def contains(self, path):
        return self.root is not None and (path == self.root or self.root in path.parents)

    def _open_log(self):
        p = self.log_path
        if p.exists() or p.is_symlink():
            st = p.lstat()
            if self._link(st) or not _stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
                raise ValueError('unsafe audit sink')
        flags = _os.O_WRONLY | _os.O_APPEND | _os.O_CREAT | getattr(_os, 'O_NOFOLLOW', 0) | getattr(_os, 'O_CLOEXEC', 0) | getattr(_os, 'O_NONBLOCK', 0)
        fd = _os.open(p, flags, 0o600)
        try:
            st = _os.fstat(fd)
            if not _stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
                raise ValueError('unsafe audit sink')
        except BaseException:
            _os.close(fd)
            raise
        return fd

    def deny(self, code, requested=None):
        identifier = str(_uuid.uuid4())
        event = {'event': 'workspace_incident', 'schema_version': '1.0',
                 'timestamp': _datetime.datetime.now(_datetime.timezone.utc).isoformat(),
                 'incident_id': identifier, 'tool': self.tool, 'pid': _os.getpid(),
                 'action': 'deny', 'code': code}
        if requested is not None:
            # Only explicit path values, never file contents or remote URLs/credentials.
            event['requested_path'] = str(requested)[:1024]
        payload = (_json.dumps(event, ensure_ascii=True, separators=(',', ':')) + '\n').encode('utf-8')
        try:
            if self.log_path is None:
                _sys.stderr.write(payload.decode('utf-8')); _sys.stderr.flush()
            else:
                fd = self._open_log()
                try:
                    if _os.write(fd, payload) != len(payload): raise OSError('short audit write')
                    _os.fsync(fd)
                finally: _os.close(fd)
        except (OSError, ValueError):
            event['original_code'] = code
            event['code'] = code = 'incident_log_unavailable'
            _sys.stderr.write(_json.dumps(event, ensure_ascii=True) + '\n'); _sys.stderr.flush()
        raise WorkspaceDenied(code, identifier)

    def inspect(self, path, allow_leaf_link=False):
        """Check physical path components without following any link."""
        path = _Path(path)
        if not self.enabled: return path
        if not self.contains(path): self.deny('path_outside_workspace')
        current = self.root
        parts = path.relative_to(self.root).parts
        for i, part in enumerate(parts):
            current = current / part
            try: st = current.lstat()
            except FileNotFoundError: break
            if self._link(st):
                if allow_leaf_link and i == len(parts)-1: return path
                self.deny('symlink_forbidden', self.virtual_unchecked(path))
            if _stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
                self.deny('hardlink_forbidden', self.virtual_unchecked(path))
            if not (_stat.S_ISREG(st.st_mode) or _stat.S_ISDIR(st.st_mode)):
                self.deny('special_file_forbidden', self.virtual_unchecked(path))
            if st.st_dev != self.root.stat().st_dev:
                self.deny('mount_boundary_forbidden', self.virtual_unchecked(path))
        return path

    def resolve(self, value, base=None):
        """POSIX virtual / is root; relative paths are root-based unless base is explicit."""
        if not self.enabled:
            p = _Path(value)
            if _os.environ.get('TWYLT_WORKSPACE_ROOT') and value.startswith('/'):
                return self.root / value.lstrip('/')
            return p if p.is_absolute() else (base or self.root)/p
        if not isinstance(value, str) or not value or '\x00' in value:
            self.deny('invalid_path')
        if '\\' in value or ':' in value or value.startswith('//') or value.startswith('~'):
            self.deny('invalid_path_syntax', value)
        parts = value.split('/')
        if '..' in parts: self.deny('path_outside_workspace', value)
        if _os.name == 'nt':
            reserved = {'CON','PRN','AUX','NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}
            if any(p.endswith((' ', '.')) or p.split('.')[0].upper() in reserved for p in parts if p not in {'', '.'}):
                self.deny('invalid_path_syntax', value)
        start = self.root if value.startswith('/') or base is None else base
        path = start.joinpath(*(p for p in parts if p not in {'', '.'}))
        return self.inspect(path)

    def virtual_unchecked(self, path):
        if not self.contains(_Path(path)): return str(path)
        relative = _Path(path).relative_to(self.root).as_posix()
        return '/' if relative == '.' else '/' + relative

    def virtual(self, path):
        if self.enabled and not self.contains(_Path(path)): self.deny('path_outside_workspace')
        return self.virtual_unchecked(path)

    def protect_root(self, path):
        if self.enabled and path == self.root: self.deny('workspace_root_mutation_forbidden', '/')

    def tree(self, path):
        """Preflight every descendant before a recursive mutation."""
        if not self.enabled: return
        self.inspect(path)
        if not path.is_dir(): return
        stack = [path]
        while stack:
            parent = stack.pop()
            with _os.scandir(parent) as children:
                for child in children:
                    p = self.inspect(_Path(child.path))
                    if p.is_dir(): stack.append(p)

    def redact(self, value):
        if self.root is None: return str(value)
        return str(value).replace(str(self.root) + _os.sep, '/').replace(str(self.root), '/')

    def __enter__(self):
        self._token = _POLICY.set(self)
        return self

    def __exit__(self, typ, exc, tb):
        _POLICY.reset(self._token)
        # Remove host workspace prefixes from errors returned by business code.
        if self.enabled and exc is not None and not isinstance(exc, WorkspaceDenied):
            if isinstance(exc, OSError):
                if exc.filename: exc.filename = self.redact(exc.filename)
                if exc.filename2: exc.filename2 = self.redact(exc.filename2)
            exc.args = tuple(self.redact(a) if isinstance(a, str) else a for a in exc.args)
        return False

def workspace():
    active = _POLICY.get()
    return active if active is not None else Workspace()

