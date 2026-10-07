import argparse
import sys
import threading

from src.console.launcher import CONSOLE_FLAG
from src.core.logger import Logger
from src.core.plugin import Plugin


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream Dock AutoCAD plugin")
    parser.add_argument("-port", type=int, required=True)
    parser.add_argument("-pluginUUID", type=str, required=True)
    parser.add_argument("-registerEvent", type=str, required=True)
    parser.add_argument("-info", type=str, required=True)
    return parser.parse_args(argv)


def main() -> None:
    argv = sys.argv[1:]
    if argv[:1] == [CONSOLE_FLAG]:
        from src.console.app import run_console

        raise SystemExit(run_console(argv[1:]))
    args = parse_args(argv)
    Logger.info("Plugin start")
    stopped = threading.Event()
    plugin = Plugin(args.port, args.pluginUUID, args.registerEvent, args.info)

    def on_close(ws, close_status_code, close_msg) -> None:
        plugin.stop()
        stopped.set()
        Logger.info("Plugin stopped")

    plugin.ws.on_close = on_close
    stopped.wait()


if __name__ == "__main__":
    main()
