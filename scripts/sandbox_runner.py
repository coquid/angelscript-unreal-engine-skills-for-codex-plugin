#!/usr/bin/env python3
"""Own one independent Unreal validation editor without changing client settings.

This helper never builds code, starts Codex, or invokes authored tests. A TCP
listener is reported as ready for a probe, never as a passed MCP/editor check.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time


class RunnerError(RuntimeError):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def powershell_json(script):
    completed = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
         "$ErrorActionPreference='Stop'; " + script],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    if completed.returncode:
        raise RunnerError(completed.stderr.strip() or 'Process inspection failed')
    return json.loads(completed.stdout) if completed.stdout.strip() else None


def process_info(process_id):
    process_id = int(process_id)
    return powershell_json(
        f'$p = Get-CimInstance Win32_Process -Filter "ProcessId = {process_id}"; '
        'if ($null -ne $p) { [pscustomobject]@{pid=[int]$p.ProcessId; '
        'executable=$p.ExecutablePath; command_line=$p.CommandLine; '
        'created=$p.CreationDate.ToUniversalTime().ToString("o")} | ConvertTo-Json -Compress }'
    )


def port_owners(port):
    value = powershell_json(
        '@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | '
        f'Where-Object LocalPort -eq {int(port)} | '
        'Select-Object -ExpandProperty OwningProcess -Unique) | ConvertTo-Json -Compress'
    )
    return [] if value is None else value if isinstance(value, list) else [value]


def same_path(left, right):
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(Path(right).resolve()))


def require_owned(state, current, allow_terminating=False):
    if not current:
        return
    if current['pid'] != state['pid'] or current['created'] != state['created']:
        raise RunnerError('Recorded process identity changed; refusing to control this PID')
    executable = current.get('executable')
    command_line = current.get('command_line')
    if ((executable and not same_path(executable, state['editor']))
            or (command_line and command_line != state['command_line'])):
        raise RunnerError('Recorded process identity changed; refusing to control this PID')
    if not executable or not command_line:
        # 종료 중 CIM 필드가 비어도 같은 PID/생성 시각이면 조회만 계속한다. 제어 전에는 전체 신원이 필요하다.
        if allow_terminating:
            return
        raise RunnerError('Process identity is incomplete; refusing to control this PID')
    if str(Path(state['project']).resolve()).casefold() not in command_line.casefold():
        raise RunnerError('Recorded project is absent from the process command line')


def resolve_inputs(args):
    project = Path(args.project).resolve()
    if project.is_dir():
        candidates = list(project.glob('*.uproject'))
        if len(candidates) != 1:
            raise RunnerError('--project must identify exactly one .uproject')
        project = candidates[0]
    engine = Path(args.engine).resolve()
    results = Path(args.results).resolve()
    repository = Path(__file__).resolve().parents[1]
    if not project.is_file() or project.suffix != '.uproject':
        raise RunnerError('Project file does not exist')
    if project.is_relative_to(repository) or results.is_relative_to(repository):
        raise RunnerError('Validation project and results must be outside the plugin repository')
    if not results.is_relative_to(project.parent / 'Saved'):
        raise RunnerError('Results must be below the external project Saved directory')
    if not 1024 <= args.port <= 65535:
        raise RunnerError('Use an explicit unprivileged local MCP port')
    editor = engine / 'Binaries/Win64/UnrealEditor.exe'
    if not editor.is_file():
        raise RunnerError(f'Existing editor binary is missing: {editor}; no build was attempted')
    if args.codex_executable and not Path(args.codex_executable).resolve().is_file():
        raise RunnerError('The explicitly supplied Codex executable does not exist')
    return project, engine, results, editor


def preflight(args):
    if os.name != 'nt':
        raise RunnerError('This editor lifecycle helper currently supports Windows only')
    project, engine, results, editor = resolve_inputs(args)
    descriptor = json.loads(project.read_text(encoding='utf-8-sig'))
    if descriptor.get('Modules'):
        raise RunnerError('This validation profile requires a content/AS project without native game modules')
    engine_modules = json.loads((engine / 'Binaries/Win64/UnrealEditor.modules').read_text(encoding='utf-8-sig'))
    plugin_evidence = []
    for module_file in sorted((project.parent / 'Plugins').glob('**/Binaries/Win64/UnrealEditor.modules')):
        modules = json.loads(module_file.read_text(encoding='utf-8-sig'))
        if not modules.get('BuildId') or modules['BuildId'] != engine_modules.get('BuildId'):
            raise RunnerError(f'Local plugin binary BuildId does not match engine: {module_file}')
        for binary in modules.get('Modules', {}).values():
            if not (module_file.parent / binary).is_file():
                raise RunnerError(f'Local plugin binary is missing: {module_file.parent / binary}')
        plugin_evidence.append({'modules': str(module_file), 'build_id': modules['BuildId']})
    enabled = {item['Name'] for item in descriptor.get('Plugins', []) if item.get('Enabled')}
    required = {'Angelscript', 'EmmsUI', 'ModelContextProtocol', 'ToolsetRegistry', 'EditorToolset', 'AutomationTestToolset', 'SlateInspectorToolset', 'PythonScriptPlugin'}
    if required - enabled:
        raise RunnerError('Missing required enabled plugins: ' + ', '.join(sorted(required - enabled)))
    return {
        'timestamp': utc_now(), 'status': 'preflight_passed', 'project': str(project),
        'engine': str(engine), 'editor': str(editor), 'port': args.port,
        'endpoint': f'http://127.0.0.1:{args.port}/mcp', 'results': str(results),
        'codex_executable': str(Path(args.codex_executable).resolve()) if args.codex_executable else None,
        'engine_build_id': engine_modules.get('BuildId'), 'local_plugin_binaries': plugin_evidence,
        'authored_tests': 'not_run', 'editor_behavior': 'not_checked',
    }


@contextmanager
def lifecycle_lock(results):
    results.mkdir(parents=True, exist_ok=True)
    path = results / 'lifecycle.lock'
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RunnerError(f'Another lifecycle operation holds {path}; inspect before removing a stale lock') from error
    try:
        os.write(descriptor, str(os.getpid()).encode('ascii'))
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)


def load_state(results):
    path = results / 'editor-state.json'
    if not path.is_file():
        raise RunnerError(f'No editor ownership record: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def inspect_state(args):
    project, engine, results, editor = resolve_inputs(args)
    state = load_state(results)
    if (not same_path(state['project'], project) or not same_path(state['editor'], editor)
            or state['port'] != args.port):
        raise RunnerError('Requested target does not match the saved ownership record')
    current = process_info(state['pid'])
    require_owned(state, current)
    owners = port_owners(args.port)
    return state, current, owners


def stop_owned(state, force=False, grace=15):
    current = process_info(state['pid'])
    require_owned(state, current)
    if current:
        powershell_json(
            f'$p = Get-Process -Id {int(state["pid"])} -ErrorAction Stop; '
            '$p.CloseMainWindow() | ConvertTo-Json -Compress'
        )
        deadline = time.monotonic() + grace
        while time.monotonic() < deadline:
            current = process_info(state['pid'])
            require_owned(state, current, allow_terminating=True)
            if not current:
                break
            time.sleep(0.5)
        if current:
            if not force and not state.get('nullrhi'):
                raise RunnerError('Editor still running after normal close; save work and retry, or explicitly use --force-after-grace')
            current = process_info(state['pid'])
            require_owned(state, current)
            if current:
                powershell_json(f'Stop-Process -Id {int(state["pid"])} -Force -ErrorAction Stop')
                for _ in range(20):
                    current = process_info(state['pid'])
                    require_owned(state, current, allow_terminating=True)
                    if current is None:
                        break
                    time.sleep(0.25)
    current = process_info(state['pid'])
    require_owned(state, current, allow_terminating=True)
    owners = port_owners(state['port'])
    state.update({'cleanup_checked_at': utc_now(), 'status': 'stopped' if not current and not owners else 'stop_failed',
                  'port_owners_after_stop': owners})
    if not current:
        state['stopped_at'] = utc_now()
    write_json(Path(state['results']) / 'editor-state.json', state)
    if current or owners:
        raise RunnerError('Editor cleanup is incomplete or the port has another owner; inspect the recorded state')
    return state



def cleanup_failed_start(process, state, results, run, startup_error, port):
    report = {'startup_error': f'{type(startup_error).__name__}: {startup_error}',
              'ownership_cleanup_error': None, 'handle_cleanup_error': None,
              'owned_process_returncode': None, 'port_owners_after_cleanup': None,
              'port_inspection_error': None, 'record_errors': []}
    if state:
        try:
            stop_owned(state, force=True, grace=3)
        except BaseException as error:
            report['ownership_cleanup_error'] = f'{type(error).__name__}: {error}'
    if process:
        try:
            if process.poll() is None:
                # 이 호출의 Popen 핸들만 사용하므로 CIM 실패나 PID 재사용이 다른 프로세스 종료로 이어지지 않는다.
                process.terminate()
                process.wait(timeout=15)
            report['owned_process_returncode'] = process.poll()
        except BaseException as error:
            report['handle_cleanup_error'] = f'{type(error).__name__}: {error}'
    try:
        report['port_owners_after_cleanup'] = port_owners(port)
    except BaseException as error:
        report['port_inspection_error'] = f'{type(error).__name__}: {error}'
    exited = process is None or report['owned_process_returncode'] is not None
    port_released = report['port_owners_after_cleanup'] == []
    report['status'] = 'startup_failed_cleaned_up' if exited and port_released else 'startup_failed_cleanup_incomplete'
    report['cleanup_checked_at'] = utc_now()
    if state:
        state.update({'status': report['status'], 'startup_cleanup': report,
                      'cleanup_checked_at': report['cleanup_checked_at'],
                      'port_owners_after_stop': report['port_owners_after_cleanup']})
        if exited:
            state['stopped_at'] = report['cleanup_checked_at']
        try:
            write_json(results / 'editor-state.json', state)
        except BaseException as error:
            report['record_errors'].append(f'ownership record: {type(error).__name__}: {error}')
    try:
        write_json(run / 'startup-failure.json', report)
    except BaseException as error:
        report['record_errors'].append(f'failure record: {type(error).__name__}: {error}')
    return report


def start(args):
    evidence = preflight(args)
    project, engine, results, editor = resolve_inputs(args)
    with lifecycle_lock(results):
        state_path = results / 'editor-state.json'
        if state_path.exists():
            previous = load_state(results)
            old_process = process_info(previous['pid'])
            if old_process:
                raise RunnerError('A recorded editor PID is still alive; use status/stop before another start')
        owners = port_owners(args.port)
        if owners:
            raise RunnerError(f'MCP port already owned by PID(s) {owners}; no process was changed')
        token = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        run = results / token
        run.mkdir(parents=True)
        argv = [str(editor), str(project), '/Engine/Maps/Entry', '-Multiprocess',
                '-as-development-mode', '-as-exit-on-error', '-as-skip-write-bind-db', '-asdebugport=0',
                '-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False',
                '-ini:Engine:[/Script/PythonScriptPlugin.PythonScriptPluginSettings]:bRemoteExecution=False',
                '-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorLoadingSavingSettings]:RestoreOpenAssetTabsOnRestart=NeverRestore',
                '-ini:Engine:[ConsoleVariables]:HomeScreen.EnableHomeScreen=0',
                '-ModelContextProtocolStartServer', f'-ModelContextProtocolPort={args.port}',
                '-NoSound', '-nosplash', '-nop4', '-stdout', '-FullStdOutLogOutput',
                f'-ABSLOG={run / "editor.log"}']
        if args.nullrhi:
            argv.extend(['-NullRHI', '-unattended'])
        else:
            argv.extend(['-windowed', '-ResX=1440', '-ResY=900'])
        write_json(run / 'preflight.json', evidence)
        state = None
        process = None
        try:
            with (run / 'stdout.log').open('wb') as output:
                process = subprocess.Popen(argv, cwd=str(project.parent), stdout=output, stderr=subprocess.STDOUT,
                                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            current = process_info(process.pid)
            if current is None:
                raise RunnerError(f'Editor exited during startup; see {run}')
            state = {**evidence, **current, 'arguments': argv, 'launch_time': utc_now(),
                     'run_directory': str(run), 'nullrhi': args.nullrhi, 'status': 'starting'}
            require_owned(state, current)
            write_json(state_path, state)
            deadline = time.monotonic() + args.startup_timeout
            while time.monotonic() < deadline:
                current = process_info(process.pid)
                if not current:
                    raise RunnerError(f'Editor exited before MCP listened; see {run}')
                require_owned(state, current)
                owners = port_owners(args.port)
                if owners:
                    if set(owners) != {process.pid}:
                        raise RunnerError('Port ownership changed to another process during startup')
                    state.update({'status': 'ready_for_mcp_probe', 'listener_verified_at': utc_now()})
                    write_json(state_path, state)
                    return state
                time.sleep(1)
            raise RunnerError(f'Timed out waiting for the owned MCP listener; see {run}')
        except BaseException as startup_error:
            startup_error.startup_cleanup = cleanup_failed_start(process, state, results, run, startup_error, args.port)
            startup_error.add_note('Startup cleanup: ' + json.dumps(startup_error.startup_cleanup))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'start', 'status', 'stop'))
    parser.add_argument('--project', required=True, help='External .uproject file or its directory')
    parser.add_argument('--engine', required=True, help='Existing Engine directory')
    parser.add_argument('--codex-executable', help='Optional explicit client binary recorded for the validation session; never launched')
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--results', required=True, help='Directory below the external project Saved/')
    parser.add_argument('--nullrhi', action='store_true', help='No visual verification is possible in this mode')
    parser.add_argument('--startup-timeout', type=float, default=120)
    parser.add_argument('--force-after-grace', action='store_true', help='Allow forced shutdown of the verified owned GUI editor after graceful close')
    args = parser.parse_args()
    if not 1 <= args.startup_timeout <= 600:
        parser.error('--startup-timeout must be between 1 and 600 seconds')
    try:
        if args.action == 'preflight':
            result = preflight(args)
        elif args.action == 'start':
            result = start(args)
        elif args.action == 'status':
            state, current, owners = inspect_state(args)
            result = {'record': state, 'process_alive': current is not None, 'port_owners': owners,
                      'owned_listener': bool(current) and set(owners) == {state['pid']}}
        else:
            _, _, results, _ = resolve_inputs(args)
            with lifecycle_lock(results):
                state, _, _ = inspect_state(args)
                result = stop_owned(state, force=args.force_after_grace)
        print(json.dumps(result, indent=2))
        return 0
    except (RunnerError, OSError, ValueError, subprocess.SubprocessError) as error:
        failure = {'status': 'failed', 'error': str(error), 'authored_tests': 'not_run'}
        if hasattr(error, 'startup_cleanup'):
            failure['startup_cleanup'] = error.startup_cleanup
        print(json.dumps(failure), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
