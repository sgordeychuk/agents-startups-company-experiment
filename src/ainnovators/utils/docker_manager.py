"""Docker container management for prototypes."""

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DockerManager:
    """Manage Docker containers for prototype deployment."""

    def __init__(self, prototype_dir: Path | str) -> None:
        """
        Initialize Docker manager.

        Args:
            prototype_dir: Path to the prototype directory containing docker-compose.yml
        """
        self.prototype_dir = Path(prototype_dir)
        self.project_name = self.prototype_dir.parent.name  # experiment name
        self._last_error: dict[str, Any] = {}

    def _run_docker_compose(
        self,
        *args: str,
        timeout: int = 300,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """
        Run a docker compose command.

        Args:
            *args: Command arguments after 'docker compose'
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess result
        """
        cmd = ["docker", "compose", "-p", self.project_name, *args]
        logger.debug(f"Running: {' '.join(cmd)}")

        return subprocess.run(
            cmd,
            cwd=self.prototype_dir,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )

    def build(self) -> bool:
        """
        Build Docker images for the prototype.

        Returns:
            True if build succeeded, False otherwise
        """
        if not (self.prototype_dir / "docker-compose.yml").exists():
            self._last_error = {
                "phase": "build",
                "error": f"No docker-compose.yml found in {self.prototype_dir}",
            }
            logger.error(f"No docker-compose.yml found in {self.prototype_dir}")
            return False

        try:
            logger.info(f"Building Docker images in {self.prototype_dir}")
            result = self._run_docker_compose("build", timeout=600)

            if result.returncode != 0:
                self._last_error = {
                    "phase": "build",
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                    "returncode": result.returncode,
                }
                logger.error(f"Docker build failed: {result.stderr}")
                return False

            logger.info("Docker build completed successfully")
            return True

        except subprocess.TimeoutExpired:
            self._last_error = {
                "phase": "build",
                "error": "Docker build timed out (10 minutes)",
            }
            logger.error("Docker build timed out (10 minutes)")
            return False
        except FileNotFoundError:
            self._last_error = {
                "phase": "build",
                "error": "docker compose command not found. Is Docker installed?",
            }
            logger.error("docker compose command not found. Is Docker installed?")
            return False
        except Exception as e:
            self._last_error = {
                "phase": "build",
                "error": str(e),
            }
            logger.error(f"Docker build error: {e}")
            return False

    def start(self) -> bool:
        """
        Start Docker containers in detached mode.

        Returns:
            True if containers started, False otherwise
        """
        try:
            logger.info(f"Starting containers for {self.project_name}")
            result = self._run_docker_compose("up", "-d", timeout=120)

            if result.returncode != 0:
                self._last_error = {
                    "phase": "start",
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                    "returncode": result.returncode,
                }
                logger.error(f"Failed to start containers: {result.stderr}")
                return False

            logger.info("Containers started successfully")
            logger.info("Frontend: http://localhost:3000")
            logger.info("Backend:  http://localhost:8000")
            return True

        except subprocess.TimeoutExpired:
            self._last_error = {
                "phase": "start",
                "error": "Container startup timed out",
            }
            logger.error("Container startup timed out")
            return False
        except Exception as e:
            self._last_error = {
                "phase": "start",
                "error": str(e),
            }
            logger.error(f"Failed to start containers: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop and remove Docker containers.

        Returns:
            True if containers stopped, False otherwise
        """
        try:
            logger.info(f"Stopping containers for {self.project_name}")
            result = self._run_docker_compose("down", timeout=60)

            if result.returncode != 0:
                logger.error(f"Failed to stop containers: {result.stderr}")
                return False

            logger.info("Containers stopped successfully")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Container shutdown timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to stop containers: {e}")
            return False

    def status(self) -> dict[str, any]:
        """
        Get container status.

        Returns:
            Dictionary with status info:
            - running: bool - whether containers are running
            - services: list - service status details
            - error: str - error message if any
        """
        try:
            result = self._run_docker_compose("ps", "--format", "json", timeout=30)

            if result.returncode != 0:
                return {
                    "running": False,
                    "services": [],
                    "error": result.stderr,
                }

            # Parse output - each line is a JSON object
            services = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        import json

                        service = json.loads(line)
                        services.append(service)
                    except json.JSONDecodeError:
                        pass

            running = any(
                s.get("State") == "running" or "Up" in s.get("Status", "") for s in services
            )

            return {
                "running": running,
                "services": services,
                "error": None,
            }

        except Exception as e:
            return {
                "running": False,
                "services": [],
                "error": str(e),
            }

    def logs(self, service: str | None = None, tail: int = 100) -> str:
        """
        Get container logs.

        Args:
            service: Optional service name (frontend/backend)
            tail: Number of lines to show

        Returns:
            Log output as string
        """
        try:
            args = ["logs", "--tail", str(tail)]
            if service:
                args.append(service)

            result = self._run_docker_compose(*args, timeout=30)
            return result.stdout + result.stderr

        except Exception as e:
            return f"Error getting logs: {e}"

    def restart(self) -> bool:
        """
        Restart containers.

        Returns:
            True if restart succeeded
        """
        return self.stop() and self.start()

    def get_last_error(self) -> dict[str, Any]:
        """
        Get details of the last failed operation.

        Returns:
            Dictionary with error details (phase, stderr, stdout, error message)
        """
        return self._last_error.copy()
