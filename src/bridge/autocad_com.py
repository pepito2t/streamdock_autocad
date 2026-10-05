import queue
import threading
import time
from concurrent.futures import Future
from typing import Any, Callable

import pythoncom
import pywintypes
import win32com.client

from src.bridge.autocad_bridge import AutocadBusy, AutocadError, AutocadNotRunning
from src.core.logger import Logger

AUTOCAD_PROGID = "AutoCAD.Application"
RPC_E_CALL_REJECTED = -2147418111
RPC_E_SERVERCALL_RETRYLATER = -2147417846
BUSY_HRESULTS = {RPC_E_CALL_REJECTED, RPC_E_SERVERCALL_RETRYLATER}
BUSY_RETRIES = 3
BUSY_RETRY_DELAY_S = 0.3
CALL_TIMEOUT_S = 10.0

Job = tuple[Callable[[], Any], Future]


class ComAutocadBridge:
    def __init__(self) -> None:
        self._jobs: "queue.Queue[Job]" = queue.Queue()
        self._app: Any = None
        self._thread = threading.Thread(target=self._worker, name="autocad-com", daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        pythoncom.CoInitialize()
        while True:
            fn, future = self._jobs.get()
            try:
                future.set_result(self._with_busy_retry(fn))
            except Exception as error:
                future.set_exception(error)

    def _with_busy_retry(self, fn: Callable[[], Any]) -> Any:
        for attempt in range(1, BUSY_RETRIES + 1):
            try:
                return fn()
            except pywintypes.com_error as error:
                if error.hresult not in BUSY_HRESULTS or attempt == BUSY_RETRIES:
                    raise self._translate(error)
                time.sleep(BUSY_RETRY_DELAY_S)
        raise AutocadBusy("AutoCAD stayed busy")

    def _translate(self, error: pywintypes.com_error) -> AutocadError:
        if error.hresult in BUSY_HRESULTS:
            return AutocadBusy(str(error))
        self._app = None
        return AutocadError(str(error))

    def _submit(self, fn: Callable[[], Any]) -> Any:
        future: Future = Future()
        self._jobs.put((fn, future))
        return future.result(timeout=CALL_TIMEOUT_S)

    def _document(self) -> Any:
        if self._app is None:
            try:
                self._app = win32com.client.GetActiveObject(AUTOCAD_PROGID)
            except pywintypes.com_error as error:
                raise AutocadNotRunning(str(error)) from error
        try:
            return self._app.ActiveDocument
        except pywintypes.com_error as error:
            self._app = None
            raise AutocadNotRunning(str(error)) from error

    def is_connected(self) -> bool:
        try:
            self._submit(self._document)
            return True
        except AutocadError:
            return False

    def run_command(self, text: str) -> None:
        self._submit(lambda: self._document().SendCommand(text))

    def get_var(self, name: str) -> Any:
        return self._submit(lambda: self._document().GetVariable(name))

    def set_var(self, name: str, value: Any) -> None:
        self._submit(lambda: self._set_variable(name, value))

    def _set_variable(self, name: str, value: Any) -> None:
        document = self._document()
        try:
            document.SetVariable(name, value)
        except pywintypes.com_error:
            if not isinstance(value, int):
                raise
            # Integer system variables are VT_I2 on the COM side; a plain int is VT_I4 and gets rejected.
            document.SetVariable(name, win32com.client.VARIANT(pythoncom.VT_I2, value))

    def get_vars(self, names: list[str]) -> dict[str, Any]:
        def read_all() -> dict[str, Any]:
            document = self._document()
            return {name: document.GetVariable(name) for name in names}

        return self._submit(read_all)

    def ensure_layer(self, name: str) -> None:
        def add_layer() -> None:
            layers = self._document().Layers
            for index in range(layers.Count):
                if layers.Item(index).Name.lower() == name.lower():
                    return
            layers.Add(name)

        self._submit(add_layer)

    def list_layers(self) -> list[str]:
        def read_names() -> list[str]:
            layers = self._document().Layers
            return sorted((layers.Item(index).Name for index in range(layers.Count)), key=str.lower)

        return self._submit(read_names)

    def prompt(self, message: str) -> None:
        self._submit(lambda: self._document().Utility.Prompt(message + "\n"))

    def reset(self) -> None:
        def drop() -> None:
            self._app = None

        self._submit(drop)
        Logger.info("[ComAutocad] connection reset")
