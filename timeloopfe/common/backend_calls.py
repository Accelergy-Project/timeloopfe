"""!@brief Call Timeloop from Python"""
import copy
import os
import signal
import subprocess
import sys
from typing import Any, List, Optional, Dict, Tuple, Union
import logging
from accelergy.utils.yaml import to_yaml_string
import psutil
from .base_specification import BaseSpecification

DELAYED_IMPORT_DONE = False


def delayed_import():
    global DELAYED_IMPORT_DONE
    if DELAYED_IMPORT_DONE:
        return
    global v3spec, v4spec, v4_to_v3

    from ..v3 import specification as current_import

    v3spec = current_import
    from ..v4 import specification as current_import

    v4spec = current_import
    from .version_transpilers import v4_to_v3 as current_import

    v4_to_v3 = current_import


def _pre_call(
    specification: BaseSpecification,
    output_dir: str,
    extra_input_files: Optional[List[str]] = None,
    for_model: bool = False,
) -> Tuple[List[str], str]:
    """!@brief Prepare to call Timeloop or Accelergy from Python
    !@param specification The specification with which to call Timeloop.
    !@param output_dir The directory to run Timeloop in.
    !@param extra_input_files A list of extra input files to pass to Timeloop.
    !@param for_model Whether the result is for Timeloop model or mapper
    """
    delayed_import()
    specification = specification._process()
    if specification.processors and not specification._processors_run:
        raise RuntimeError(
            "Specification has not been processed yet. Please call "
            "spec.process() before calling Timeloop or Accelergy."
        )

    if isinstance(specification, v3spec.Specification):
        input_content = to_yaml_string(specification)
    elif isinstance(specification, v4spec.Specification):
        input_content = v4_to_v3.transpile(specification, for_model=for_model)
        input_content = to_yaml_string(input_content)
    else:
        raise TypeError(f"Can not call Timeloop with {type(specification)}")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "inputs"), exist_ok=True)
    with open(os.path.join(output_dir, "inputs", "input.yaml"), "w") as f:
        f.write(input_content)

    input_paths = [os.path.join(output_dir, "inputs", "input.yaml")] + (
        extra_input_files or []
    )
    input_paths = [os.path.abspath(f) for f in input_paths]
    return (
        input_paths,
        output_dir,
    )


def _call(
    call: str,
    input_paths: List[str],
    output_dir: str,
    environment: Optional[Dict[str, str]] = None,
    dump_intermediate_to: Optional[str] = None,
    log_to: Optional[str] = None,
    return_proc: bool = False,
) -> Union[int, subprocess.Popen]:
    """!@brief Call a Timeloop or Accelergy command from Python
    !@param call Which command to call.
    !@param input_content The content of the input file.
    !@param output_dir The directory to run Timeloop in.
    !@param environment A dictionary of environment variables to pass.
    !@param dump_intermediate_to If not None, dump the input content to this
                                 file before calling.
    !@param log_to If not None, log the output of the call to this file or
                   file-like object.
    !@param return_proc If True, return the subprocess.Popen object instead of
                        the return code.
    !@return The return code of the call, or the subprocess.Popen object if
             return_proc is True.
    """
    os.makedirs(output_dir, exist_ok=True)
    if dump_intermediate_to is None:
        dump_intermediate_to = os.path.join(output_dir, f"input.yaml")
    logging.info(f"Calling {call} with input {input_paths} and output {output_dir}")

    ifiles = [os.path.abspath(x) for x in input_paths]
    for i, f in enumerate(ifiles):
        # If not quote enclosed, add quotes
        if not f.startswith('"') and not f.endswith('"'):
            ifiles[i] = '"' + f + '"'

    envstr = " ".join(str(k) + "=" + str(v) for k, v in (environment or {}).items())

    tlcmd = f'cd "{output_dir}" ; {envstr} {call} {" ".join(ifiles)}'
    logging.info("Calling Timeloop: %s", tlcmd)
    if isinstance(log_to, str):
        log_to = open(log_to, "w")
    if log_to is None:
        # Send to the current stdout
        log_to = sys.stdout
    proc = subprocess.Popen(tlcmd, shell=True, stdout=log_to, stderr=subprocess.STDOUT)
    if return_proc:
        return proc
    else:
        # Wait for the subprocess. If there is a ctrl-c, send it to the proc.
        while True:
            try:
                return proc.wait()
            except KeyboardInterrupt:
                proc.send_signal(sig=signal.SIGINT)


def call_mapper(
    specification: BaseSpecification,
    output_dir: str,
    environment: Optional[Dict[str, str]] = None,
    extra_input_files: Optional[List[str]] = None,
    dump_intermediate_to: Optional[str] = None,
    log_to: Optional[Union[str, Any]] = None,
    return_proc: bool = False,
    legacy_timeloop: bool = False,
) -> Union[int, subprocess.Popen]:
    """!@brief Call Timeloop Mapper from Python
    !@param specification The specification with which to call Timeloop.
    !@param input_content The content of the input file.
    !@param output_dir The directory to run Timeloop in.
    !@param environment A dictionary of environment variables to pass to
                        Timeloop.
    !@param extra_input_files A list of extra input files to pass to Timeloop.
    !@param dump_intermediate_to If not None, dump the input content to this
                                 file before calling Timeloop.
    !@param log_to If not None, log the output of the Timeloop call to this
                   file or file-like object.
    !@param return_proc If True, return the subprocess.Popen object instead of
                        the return code.
    !@param legacy_timeloop If True, use the legacy Timeloop command.
    !@return The return code of the call, or the subprocess.Popen object if
             return_proc is True.
    """
    input_paths, output_dir = _pre_call(
        specification, output_dir, extra_input_files, for_model=False
    )

    mapper = "timeloop_mapper" if not legacy_timeloop else "timeloop-mapper"
    return _call(
        mapper,
        input_paths=input_paths,
        output_dir=output_dir,
        environment=environment,
        dump_intermediate_to=dump_intermediate_to,
        log_to=log_to,
        return_proc=return_proc,
    )


def call_model(
    specification: BaseSpecification,
    output_dir: str,
    environment: Optional[Dict[str, str]] = None,
    extra_input_files: Optional[List[str]] = None,
    dump_intermediate_to: Optional[str] = None,
    log_to: Optional[Union[str, Any]] = None,
    return_proc: bool = False,
    legacy_timeloop: bool = False,
) -> Union[int, subprocess.Popen]:
    """!@brief Call Timeloop Model from Python
    !@param specification The specification with which to call Timeloop.
    !@param input_content The content of the input file.
    !@param output_dir The directory to run Timeloop in.
    !@param environment A dictionary of environment variables to pass to
                        Timeloop.
    !@param extra_input_files A list of extra input files to pass to Timeloop.
    !@param dump_intermediate_to If not None, dump the input content to this
                                 file before calling Timeloop.
    !@param log_to If not None, log the output of the Timeloop call to this
                   file or file-like object.
    !@param return_proc If True, return the subprocess.Popen object instead of
                        the return code.
    !@param legacy_timeloop If True, use the legacy Timeloop command.
    !@return The return code of the call, or the subprocess.Popen object if
             return_proc is True.
    """
    input_paths, output_dir = _pre_call(
        specification, output_dir, extra_input_files, for_model=True
    )

    model = "timeloop_model" if not legacy_timeloop else "timeloop-model"
    return _call(
        model,
        input_paths=input_paths,
        output_dir=output_dir,
        environment=environment,
        dump_intermediate_to=dump_intermediate_to,
        log_to=log_to,
        return_proc=return_proc,
    )


def call_accelergy_verbose(
    specification: BaseSpecification,
    output_dir: str,
    environment: Optional[Dict[str, str]] = None,
    extra_input_files: Optional[List[str]] = None,
    dump_intermediate_to: Optional[str] = None,
    log_to: Optional[Union[str, Any]] = None,
    return_proc: bool = False,
) -> Union[int, subprocess.Popen]:
    """!@brief Call Timeloop Mapper from Python
    !@param specification The specification with which to call Timeloop.
    !@param input_content The content of the input file.
    !@param output_dir The directory to run Timeloop in.
    !@param environment A dictionary of environment variables to pass to
                        Timeloop.
    !@param extra_input_files A list of extra input files to pass to Timeloop.
    !@param dump_intermediate_to If not None, dump the input content to this
                                 file before calling Timeloop.
    !@param log_to If not None, log the output of the Timeloop call to this
                   file or file-like object.
    !@param return_proc If True, return the subprocess.Popen object instead of
                        the return code.
    !@return The return code of the call, or the subprocess.Popen object if
             return_proc is True.
    """
    input_paths, output_dir = _pre_call(
        specification, output_dir, extra_input_files, for_model=False
    )

    return _call(
        "accelergy -v",
        input_paths=input_paths,
        output_dir=output_dir,
        environment=environment,
        dump_intermediate_to=dump_intermediate_to,
        log_to=log_to,
        return_proc=return_proc,
    )


def call_stop(
    proc: Optional[subprocess.Popen] = None,
    max_wait_time: Optional[int] = None,
    force: bool = False,
):
    """!@brief Stop Timeloop subprocesses.
    !@param proc The subprocesses to stop. If None, stop all Timeloop subprocesses.
    !@param max_wait_time The maximum time to wait for the process to stop.
                          If None, do not wait. If 0, wait forever.
    !@param force If True, force kill the process.
    """

    def stop_single(p, f):
        if f:
            logging.info("  Force killing process PID %s", p.pid)
            p.kill()
        else:
            logging.info("  Sending SIGINT to process PID %s", p.pid)
            p.send_signal(signal.SIGINT)

    def stop_proc(p, f):
        logging.info("Stopping %s", p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        for child in children:
            stop_single(child, f)
        stop_single(p, f)

    procs = []
    if proc is None:
        procs = [p for p in psutil.process_iter() if "timeloop" in p.name()]
        procs += [p for p in psutil.process_iter() if "accelergy" in p.name()]
    else:
        procs = [proc]

    for p in procs:
        try:
            stop_proc(p, force)
        except psutil.NoSuchProcess:
            pass
    if max_wait_time is not None:
        for p in procs:
            try:
                p.wait(None if max_wait_time == 0 else max_wait_time)
            except psutil.NoSuchProcess:
                pass


def accelergy_app(
    specification: BaseSpecification,
    output_dir: str,
    extra_input_files: Optional[List[str]] = None,
) -> "AccelergyInvocationResult":
    """!@brief Call Accelergy from Python
    !@param specification The specification with which to call Accelergy.
    !@param output_dir The directory to run Accelergy in.
    !@param extra_input_files A list of extra input files to pass to Accelergy.
    !@return The AccelergyInvocationResult object.
    """
    try:
        from pytimeloop.accelergy_interface import invoke_accelergy
    except:
        raise ImportError(
            "pytimeloop is not installed. To call accelergy_app, please install pytimeloop. "
            "Alternatively, you can use the call_accelergy_verbose function directly."
        )

    input_paths, output_dir = _pre_call(specification, output_dir, extra_input_files)
    return invoke_accelergy(input_paths, output_dir)


def to_mapper_app(
    specification: BaseSpecification,
    output_dir: str,
    extra_input_files: Optional[List[str]] = None,
):
    try:
        from pytimeloop.app import MapperApp
    except ImportError:
        raise ImportError(
            "pytimeloop is not installed. To create a mapper app, please install pytimeloop. "
            "Alternatively, you can use the call_mapper function directly."
        )

    input_paths, output_dir = _pre_call(
        specification, output_dir, extra_input_files, for_model=False
    )
    input_agg = "".join(open(i).read() for i in input_paths)
    return MapperApp(input_agg, default_out_dir=output_dir)


def to_model_app(
    specification: BaseSpecification,
    output_dir: str,
    extra_input_files: Optional[List[str]] = None,
):
    """!@brief Call Timeloop Model from Python
    !@param specification The specification with which to call Timeloop.
    !@param output_dir The directory to run Timeloop in.
    !@param extra_input_files A list of extra input files to pass to Timeloop.
    !@return The ModelApp object.
    """
    try:
        from pytimeloop.app import ModelApp
    except ImportError:
        raise ImportError(
            "pytimeloop is not installed. To create a model app, please install pytimeloop. "
            "Alternatively, you can use the call_model function directly."
        )

    input_paths, output_dir = _pre_call(
        specification, output_dir, extra_input_files, for_model=True
    )
    input_agg = "".join(open(i).read() for i in input_paths)
    return ModelApp(input_agg, default_out_dir=output_dir)
