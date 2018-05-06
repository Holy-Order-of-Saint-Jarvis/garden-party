# coding: utf-8

import subprocess  # nosec
import sys

import click

from . import supervisor

SUPERVISOR = None


# output styles
def critical(*args):
    click.secho(*args, fg='white', bg='red', bold=True)


def info(*args):
    click.secho(*args, fg='magenta', bold=True)


@click.group()
@click.option('-c', '--config', 'config_path',
              type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              default='supervisord.ini',
              show_default=True,
              help='Path to supervisor configuration file.')
def cli(config_path):
    """
    Saint Jarvis's Garden Party!
    """
    global SUPERVISOR
    SUPERVISOR = supervisor.Supervisor.from_config(config_path)


@cli.command()
@click.option('--fail-on-running', '-X',
              is_flag=True,
              default=False,
              help='Fails if the supervisor daemon is already running.')
def start(fail_on_running):
    """
    Starts the supervisor daemon and its children, if not running.
    """
    if not SUPERVISOR.running:
        cmd = ['supervisord', '-c', SUPERVISOR._config_path]
        rc = subprocess.check_call(cmd)     # nosec
        sys.exit(rc)
    else:
        msg = 'supervisor daemon already started'
        if fail_on_running:
            critical(msg)
            sys.exit(255)
        else:
            info(msg)
            sys.exit(0)


@cli.command()
def graph_process_states():
    """
    Generates a Dot graph of currently-defined process states and their
    transitions.
    """
    click.echo('digraph {')
    for base, targets in supervisor.PROCESS_STATES.items():
        for target in targets:
            click.echo(f'\t{base.name} -> {target.name}')
    click.echo('}')


@cli.command()
def stop():
    """
    Stops the supervisor daemon and its children, if running.
    """
    if SUPERVISOR.running:
        cmd = ['supervisorctl', '-c', SUPERVISOR._config_path, 'shutdown']
        rc = subprocess.check_call(cmd)     # nosec
        sys.exit(rc)
    else:
        click.secho('supervisor daemon is not running',
                    fg='white', bg='red', bold=True)
        sys.exit(255)


@cli.command()
def health():
    """
    Interrogates the current health of the system.
    """
    states = SUPERVISOR.get_process_states()
    all_running = all(st[0] for st in states.values())
    info('System health:')
    maxlen = max(len(k) for k in states)
    tabs, _ = divmod(maxlen, 4)
    padlen = 4 * tabs + 4
    for name in sorted(states):
        running, label = states[name]
        click.echo(f'  {name:{padlen}} ', nl=False)
        click.secho(label, fg='green' if running else 'red', bold=True)

    if not all_running:
        sys.exit(255)
