from src.bridge.autocad_bridge import AutocadBusy, AutocadError, AutocadNotRunning
from src.macros.macro import InvalidMacro

NOT_RUNNING = "AutoCAD n'est pas ouvert, ou aucun dessin n'est actif."
BUSY = "AutoCAD est occupé : terminez la commande ou la boîte de dialogue en cours, puis réessayez."
GENERIC = "AutoCAD a refusé l'opération"


def describe_error(error: Exception) -> str:
    if isinstance(error, AutocadNotRunning):
        return NOT_RUNNING
    if isinstance(error, AutocadBusy):
        return BUSY
    if isinstance(error, InvalidMacro):
        return f"Macro invalide : {error}"
    if isinstance(error, AutocadError):
        return f"{GENERIC} : {error}"
    return str(error)
