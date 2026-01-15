"""Experiment logging utility to capture all logs to experiment folder."""

import logging
import sys
from contextlib import contextmanager
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path


class TeeWriter:
    """
    A writer that duplicates output to both the original stream and a file.

    This ensures terminal output is mirrored to the log file.
    """

    def __init__(self, original: TextIOWrapper, log_file: TextIOWrapper) -> None:
        self.original = original
        self.log_file = log_file

    def write(self, text: str) -> int:
        self.original.write(text)
        self.log_file.write(text)
        self.log_file.flush()
        return len(text)

    def flush(self) -> None:
        self.original.flush()
        self.log_file.flush()

    def fileno(self) -> int:
        return self.original.fileno()

    def isatty(self) -> bool:
        return self.original.isatty()


class ExperimentLogger:
    """
    Manages experiment-specific logging.

    Captures all Python logging output and stdout/stderr to a single log file
    in the experiment's logs folder, while still displaying in the terminal.
    """

    def __init__(self, experiment_dir: Path) -> None:
        """
        Initialize the experiment logger.

        Args:
            experiment_dir: Path to the experiment directory
        """
        self.experiment_dir = experiment_dir
        self.logs_dir = experiment_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = self.logs_dir / f"experiment_{timestamp}.log"

        self._log_file: TextIOWrapper | None = None
        self._file_handler: logging.FileHandler | None = None
        self._original_stdout: TextIOWrapper | None = None
        self._original_stderr: TextIOWrapper | None = None
        self._is_active = False

    def start(self) -> None:
        """Start capturing logs to the experiment log file."""
        if self._is_active:
            return

        self._log_file = open(self.log_file_path, "w", encoding="utf-8")

        self._write_header()

        self._file_handler = logging.FileHandler(self.log_file_path, mode="a", encoding="utf-8")
        self._file_handler.setLevel(logging.DEBUG)
        self._file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        root_logger = logging.getLogger()
        root_logger.addHandler(self._file_handler)

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = TeeWriter(self._original_stdout, self._log_file)
        sys.stderr = TeeWriter(self._original_stderr, self._log_file)

        self._is_active = True

    def _write_header(self) -> None:
        """Write header information to the log file."""
        if not self._log_file:
            return

        header = [
            "=" * 80,
            f"EXPERIMENT LOG: {self.experiment_dir.name}",
            f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
        ]
        self._log_file.write("\n".join(header))
        self._log_file.write("\n")
        self._log_file.flush()

    def stop(self) -> None:
        """Stop capturing logs and restore original streams."""
        if not self._is_active:
            return

        if self._original_stdout:
            sys.stdout = self._original_stdout
        if self._original_stderr:
            sys.stderr = self._original_stderr

        if self._file_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self._file_handler)
            self._file_handler.close()

        self._write_footer()

        if self._log_file:
            self._log_file.close()

        self._is_active = False

    def _write_footer(self) -> None:
        """Write footer information to the log file."""
        if not self._log_file:
            return

        footer = [
            "",
            "=" * 80,
            f"EXPERIMENT COMPLETED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
        ]
        self._log_file.write("\n".join(footer))
        self._log_file.write("\n")
        self._log_file.flush()

    @property
    def log_path(self) -> Path:
        """Get the path to the log file."""
        return self.log_file_path


@contextmanager
def experiment_logging(experiment_dir: Path):
    """
    Context manager for experiment logging.

    Usage:
        with experiment_logging(Path("./experiments/my_experiment")):
            # All logs and print statements will be captured
            print("This goes to terminal AND log file")
            logger.info("This also goes to both")
    """
    exp_logger = ExperimentLogger(experiment_dir)
    exp_logger.start()
    try:
        yield exp_logger
    finally:
        exp_logger.stop()
