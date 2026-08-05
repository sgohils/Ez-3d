import json
import logging
import os
import tarfile
import io

import docker
from docker.errors import DockerException, ContainerError, APIError

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = os.getenv("CAD_SANDBOX_IMAGE", "cadquery-sandbox")
EXECUTION_TIMEOUT = 30


class SandboxExecutionError(Exception):
    def __init__(self, message: str, logs: str = ""):
        super().__init__(message)
        self.logs = logs


def _get_client() -> docker.DockerClient:
    try:
        return docker.DockerClient(base_url=os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock"))
    except DockerException as exc:
        raise SandboxExecutionError(f"Failed to connect to Docker daemon: {exc}") from exc


def _build_script_tarball(script_content: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        script_bytes = script_content.encode("utf-8")
        info = tarfile.TarInfo(name="script.py")
        info.size = len(script_bytes)
        info.mode = 0o644
        tar.addfile(info, io.BytesIO(script_bytes))
    buf.seek(0)
    return buf.read()


def execute_cadquery_script(script_content: str) -> dict:
    client = _get_client()
    tarball = _build_script_tarball(script_content)

    try:
        container = client.containers.run(
            SANDBOX_IMAGE,
            command=["--script", "/sandbox/inputs/script.py", "--result-file", "/sandbox/outputs/result.json"],
            volumes={
                "cadgen_outputs": {"bind": "/sandbox/outputs", "mode": "rw"},
            },
            mem_limit="512m",
            nano_cpus=500_000_000,
            network_disabled=True,
            read_only=True,
            tmpfs={"/tmp": "noexec,nosuid,size=64m"},
            detach=True,
            stdin_open=False,
            tty=False,
        )
    except (ContainerError, APIError) as exc:
        raise SandboxExecutionError(f"Failed to start sandbox container: {exc}") from exc

    try:
        container.put_archive("/sandbox/inputs/", tarball)
    except APIError as exc:
        container.remove(force=True)
        raise SandboxExecutionError(f"Failed to copy script into container: {exc}") from exc

    try:
        result = container.wait(timeout=EXECUTION_TIMEOUT)
        exit_code = result.get("StatusCode", -1)
        logs = container.logs().decode("utf-8", errors="replace")
    except Exception:
        container.remove(force=True)
        raise SandboxExecutionError("Execution timed out or container failed", logs="")

    try:
        archive, _ = container.get_archive("/sandbox/outputs/result.json")
        buf = io.BytesIO()
        for chunk in archive:
            buf.write(chunk)
        buf.seek(0)
        with tarfile.open(fileobj=buf, mode="r") as tar:
            member = tar.getmember("result.json")
            result_fh = tar.extractfile(member)
            execution_result = json.loads(result_fh.read().decode("utf-8"))
    except Exception as exc:
        container.remove(force=True)
        raise SandboxExecutionError(f"Failed to read execution result: {exc}", logs=logs)
    finally:
        container.remove(force=True)

    if exit_code != 0 or execution_result.get("status") == "error":
        error_msg = execution_result.get("error", f"Container exited with code {exit_code}")
        raise SandboxExecutionError(error_msg, logs=execution_result.get("logs", logs))

    execution_result["logs"] = execution_result.get("logs", "") + "\n" + logs
    return execution_result


def ensure_sandbox_image() -> None:
    client = _get_client()
    try:
        client.images.get(SANDBOX_IMAGE)
    except docker.errors.ImageNotFound:
        logger.info("Sandbox image '%s' not found, building from ./backend/sandbox", SANDBOX_IMAGE)
        raise SandboxExecutionError(
            f"Sandbox image '{SANDBOX_IMAGE}' not found. "
            "Run: docker compose build cadquery-sandbox"
        )
