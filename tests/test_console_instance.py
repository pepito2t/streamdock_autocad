import subprocess
import sys

from src.console.instance import SingleInstance
from src.console.launcher import CONSOLE_FLAG, console_command

HOLD_LOCK = """
import sys, time
from pathlib import Path
from src.console.instance import SingleInstance
instance = SingleInstance(Path(sys.argv[1]))
print(instance.acquire(), flush=True)
time.sleep(30)
"""


def test_second_instance_is_refused_while_first_holds_lock(tmp_path):
    holder = subprocess.Popen([sys.executable, "-c", HOLD_LOCK, str(tmp_path)], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "True"
        other = SingleInstance(tmp_path)
        assert other.is_running()
        assert not other.acquire()
    finally:
        holder.kill()
        holder.wait()
    assert SingleInstance(tmp_path).acquire()


def test_lock_is_released_with_the_instance(tmp_path):
    first = SingleInstance(tmp_path)
    assert first.acquire()
    first.release()
    assert not SingleInstance(tmp_path).is_running()


def test_focus_request_is_seen_once(tmp_path):
    window = SingleInstance(tmp_path)
    SingleInstance(tmp_path).request_focus()
    assert window.acquire()
    assert not window.focus_requested()
    SingleInstance(tmp_path).request_focus()
    assert window.focus_requested()
    assert not window.focus_requested()


def test_console_command_relaunches_main_in_development(tmp_path):
    command = console_command(tmp_path / "plugin.log")
    assert command[0] == sys.executable
    assert command[1].endswith("main.py")
    assert command[2:] == [CONSOLE_FLAG, str(tmp_path / "plugin.log")]
