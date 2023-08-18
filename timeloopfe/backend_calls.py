"""!@brief Call Timeloop from Python"""
import os
import signal
import subprocess
import sys
from typing import IO, Any, List, Optional, Dict, Union
import time
import logging
from . import v4spec
from . import v3spec
from .version_transpilers import v4_to_v3
from accelergy.utils.yaml import to_yaml_string
import psutil


def _call(
    call: str,
    input_content: str,
    output_dir: str,
    environment: Optional[Dict[str, str]] = None,
    extra_input_files: Optional[List[str]] = None,
    dump_intermediate_to: Optional[str] = None,
    log_to: Optional[str] = None,
    return_proc: bool = False,
) -> Union[int, subprocess.Popen]:
    """!@brief Call a Timeloop or Accelergy command from Python
    !@param call Which command to call.
    !@param input_content The content of the input file.
    !@param output_dir The directory to run Timeloop in.
    !@param environment A dictionary of environment variables to pass.
    !@param extra_input_files A list of extra input files to pass.
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
        dump_intermediate_to = (
            f'/tmp/timeloop_call_{time.strftime("%Y%m%d-%H%M%S")}.yaml'
        )
    logging.info(f"Dumping Timeloop input data to {dump_intermediate_to}")
    with open(dump_intermediate_to, "w") as f:
        f.write(input_content)
    ifiles = [dump_intermediate_to] + (extra_input_files or [])
    ifiles = [os.path.abspath(x) for x in ifiles]

    envstr = " ".join(
        str(k) + "=" + str(v) for k, v in (environment or {}).items()
    )

    tlcmd = f"cd {output_dir} ; {envstr} {call} {' '.join(ifiles)}"
    logging.info("Calling Timeloop: %s", tlcmd)
    if isinstance(log_to, str):
        log_to = open(log_to, "w")
    if log_to is None:
        # Send to the current stdout
        log_to = sys.stdout
    proc = subprocess.Popen(
        tlcmd, shell=True, stdout=log_to, stderr=subprocess.STDOUT
    )
    if return_proc:
        return proc
    else:
        # Wait for the subprocess. If there is a ctrl-c, send it to the proc.
        while True:
            try:
                return proc.wait()
            except KeyboardInterrupt:
                proc.send_signal(sig=signal.SIGINT)


def call_timeloop_mapper(
    specification: "Specification",
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
    if isinstance(specification, v3spec.specification.Specification):
        input_content = to_yaml_string(specification)
    elif isinstance(specification, v4spec.specification.Specification):
        input_content = v4_to_v3.transpile(specification, False)
        input_content = to_yaml_string(input_content)
    else:
        raise TypeError(f"Can not call Timeloop with {type(specification)}")
    mapper = "timeloop_mapper" if not legacy_timeloop else "timeloop-mapper"
    return _call(
        mapper,
        input_content=input_content,
        output_dir=output_dir,
        environment=environment,
        extra_input_files=extra_input_files,
        dump_intermediate_to=dump_intermediate_to,
        log_to=log_to,
        return_proc=return_proc,
    )


def call_timeloop_model(
    specification: "Specification",
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
    if isinstance(specification, v3spec.specification.Specification):
        input_content = to_yaml_string(specification)
    elif isinstance(specification, v4spec.specification.Specification):
        input_content = v4_to_v3.transpile(specification, True)
        input_content = to_yaml_string(input_content)
    else:
        raise TypeError(f"Can not call Timeloop with {type(specification)}")
    model = "timeloop_model" if not legacy_timeloop else "timeloop-model"
    return _call(
        model,
        input_content=input_content,
        output_dir=output_dir,
        environment=environment,
        extra_input_files=extra_input_files,
        dump_intermediate_to=dump_intermediate_to,
        log_to=log_to,
        return_proc=return_proc,
    )


def call_accelergy_verbose(
    specification: "Specification",
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
    if isinstance(specification, v3spec.specification.Specification):
        input_content = to_yaml_string(specification)
    elif isinstance(specification, v4spec.specification.Specification):
        input_content = v4_to_v3.transpile(specification, False)
        input_content = to_yaml_string(input_content)
    else:
        raise TypeError(f"Can not call Timeloop with {type(specification)}")

    return _call(
        "accelergy -v",
        input_content=input_content,
        output_dir=output_dir,
        environment=environment,
        extra_input_files=extra_input_files,
        dump_intermediate_to=dump_intermediate_to,
        log_to=log_to,
        return_proc=return_proc,
    )


def stop_timeloop(
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
