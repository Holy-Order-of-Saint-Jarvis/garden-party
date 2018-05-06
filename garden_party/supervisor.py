# coding: utf-8

import configparser
import os
from enum import IntEnum
from typing import Dict, Iterable, Set, Tuple, Type
from xmlrpc import client

import attr
from supervisor import states, xmlrpc


def _make_enum(enum_name: str, source: type) -> Type[IntEnum]:
    names = [name for name in dir(source) if name.upper() == name]
    return IntEnum(enum_name, {k: getattr(source, k) for k in names})


ProcessState = _make_enum('ProcessState', states.ProcessStates)
SupervisorState = _make_enum('SupervisorState', states.SupervisorStates)
EventListenerState = _make_enum(
        'EventListenerState', states.EventListenerStates)


PROCESS_STATES = {
    ProcessState.STARTING: {
        ProcessState.RUNNING,
        ProcessState.STOPPING,
        ProcessState.BACKOFF,
    },
    ProcessState.RUNNING: {
        ProcessState.STOPPING,
        ProcessState.EXITED,
    },
    ProcessState.STOPPING: {
        ProcessState.STOPPED,
    },
    ProcessState.STOPPED: {
        ProcessState.STARTING,
    },
    ProcessState.EXITED: {
        ProcessState.STARTING,
    },
    ProcessState.FATAL: {
        ProcessState.STARTING,
    },
    ProcessState.BACKOFF: {
        ProcessState.FATAL,
        ProcessState.STARTING,
    },
}


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Process(object):
    name: str
    group: str
    description: str
    start: int
    stop: int
    now: int
    state: ProcessState = attr.ib()
    statename: str
    stdout_logfile: str
    stderr_logfile: str
    pid: int
    exitstatus: int
    logfile: str = None
    spawnerr: str = None
    _supervisor: 'Supervisor' = None
    exitreason: str = attr.ib(init=False)
    nextstates: Set[ProcessState] = attr.ib(init=False)

    @exitreason.default
    def _exitreason(self):
        if self.exitstatus != 0:
            return os.strerror(self.exitstatus)

    @nextstates.default
    def _nextstates(self):
        return PROCESS_STATES[self.state]

    @state.validator
    def _validate_state(self, attribute, value):
        object.__setattr__(self, 'state', ProcessState(value))

    @staticmethod
    def from_supervisor(supervisor, process_dict):
        self = Process(**process_dict)
        object.__setattr__(self, '_supervisor', supervisor)
        return self

    @property
    def running(self):
        """True if the process is currently running."""
        return self.state in states.RUNNING_STATES

    @property
    def stopped(self):
        """True if the process has stopped."""
        return self.state in states.STOPPED_STATES

    @property
    def age(self):
        """Number of seconds since this process was started."""
        return self.now - self.start

    @property
    def elapsed(self):
        """Total number of seconds for which the process ran."""
        return min(self.now, self.stop) - self.start


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Supervisor(object):
    _conn: client.ServerProxy = attr.ib(repr=False)
    _config: configparser.ConfigParser = attr.ib(repr=False)
    _config_path: str = attr.ib(default=None, repr=False)

    @staticmethod
    def from_config(config: str) -> 'Supervisor':
        parser = configparser.ConfigParser(
                inline_comment_prefixes=('#', ';'),)
        parser.read(config)

        conn = Supervisor._get_connection(parser)
        return Supervisor(conn, parser, config)

    def _reconnecting(self, method, *args):
        attempts = 0
        while attempts < 3:
            try:
                return method(*args)
            except Exception:
                # something went kablooey, reconnect and try again
                conn = type(self)._get_connection(self._config)
                object.__setattr__(self, '_conn', conn)
                attempts += 1
        raise RuntimeError('could not connect to supervisor daemon')

    @staticmethod
    def _get_connection(
            config: configparser.ConfigParser) -> client.ServerProxy:
        cfg = dict(dict(config).get('supervisorctl', {}))
        try:
            transport = xmlrpc.SupervisorTransport(
                    serverurl=cfg['serverurl'],
                    username=cfg.get('username'),
                    password=cfg.get('password'),)
        except KeyError as ex:
            msg = (f"supervisor config '{config}' is missing required"
                   f' supervisorctl key {ex.args[0]}')
            raise RuntimeError(msg) from ex

        bogus = transport.serverurl
        if bogus.startswith('unix://'):
            bogus = 'http://unix-domain-socket@127.0.0.1:9001'

        conn = client.ServerProxy(bogus, transport=transport)
        return conn

    @property
    def running(self) -> bool:
        return self._state().get('statecode') == 1

    def _state(self) -> dict:
        try:
            return self._reconnecting(self._conn.supervisor.getState)
        except (BrokenPipeError, FileNotFoundError, RuntimeError):
            # the UNIX socket has been closed, supervisord is stopped
            return {'statecode': -999, 'statename': 'STOPPED'}

    def _process_info(self, name: str) -> dict:
        try:
            return self._conn.supervisor.getProcessInfo(name)
        except client.Fault:
            raise NameError(f"unknown process '{name}'")

    def _process_state(self, name: str) -> Tuple[bool, str]:
        try:
            info = self._process_info(name)
        except NameError:
            info = {'state': -1, 'statename': 'UNKNOWN'}
        state = info.get('state', -1)
        label = info.get('statename')
        running = state in states.RUNNING_STATES
        if not label:
            if running:
                label = 'RUNNING'
            elif state in states.STOPPED_STATES:
                label = 'STOPPED'
            else:
                label = 'UNKNOWN'
        return (running, label)

    def _all_programs(self):
        for section in self._config.sections():
            if section.startswith('program:'):
                yield section[8:]

    def get_process_states(
            self,
            *processes: Iterable[str]) -> Dict[str, Tuple[bool, str]]:
        if not processes:
            processes = list(self._all_programs())
        state = self._state()
        running = state.get('statecode') == 1
        label = state.get('statename', 'UNKNOWN')
        states = {'supervisord': (running, label)}
        if not running:
            # can't get states if we're not running, everything's UNKNOWN
            states.update({p: (False, 'UNKNOWN') for p in processes})
        else:
            states.update({p: self._process_state(p) for p in processes})
        return states
