import json
import typing
from typing import TextIO

_DOUBLE_SLASH = "//"


# originally authored by pydew-j
def patch_windows_utf8():
    """
    On Windows, files are opened with the system locale, not with UTF-8. This leads to problems
    with umlauts such as 'ü'. See https://dev.to/methane/python-use-utf-8-mode-on-windows-212i.
    It's not possible to set os.environ["PYTHONUTF8"] = "1" in code, because that env var is checked
    at startup time already. This function thus hackily replaces the open() function and adds
    encoding='utf8' to all text-based file opens. It would be possible to add this to every individual
    call, but it's very error-prone to forget, especially since it works on Linux and macOS.

    Also, moving this function to another module can be tricky due to import order and `open()` already
    being called in other modules. If moved, re-test on Windows.
    """

    import builtins
    import os
    import sys

    # If UTF-8 mode already set or not running on Windows: nothing to do
    if sys.platform != "win32" or os.getenv("PYTHONUTF8") == "1":
        return

    original_open = builtins.open

    # Override open() to enforce UTF-8 by default, except for binary modes.
    def utf8_open(*args, **kwargs):
        mode = args[1] if len(args) > 1 else kwargs.get("mode", "r")

        # Apply encoding only if the mode is text (not binary)
        if "b" not in mode and "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"

        return original_open(*args, **kwargs)

    # Apply the override globally
    builtins.open = utf8_open


# hacky fix for now
patch_windows_utf8()


class JSONWithCommentsDecoder(json.JSONDecoder):
    """JSON Decoder which allows comments starting with //.

    Comments are not preserved. They are simply useful to document
    input files.
    """

    def decode(self, s: str) -> typing.Any:
        # import pdb; pdb.set_trace()
        lines = s.split("\n")
        # filter out any line with leading //
        lines = (line for line in lines if not line.strip().startswith(_DOUBLE_SLASH))

        # ignore any text on a line after a //
        lines = [line.split(_DOUBLE_SLASH, maxsplit=1)[0] for line in lines]

        s = "\n".join(lines)
        return super().decode(s)


def json_loads(s: str, **kwargs) -> typing.Any:
    """Helper function to decode a JSON string.

    JSON inputs can contain comments beginning with //.

    Wrapper function for `json.loads`, with custom decoder.
    """
    return json.loads(s, cls=JSONWithCommentsDecoder, **kwargs)


def json_load(stream: TextIO, **kwargs) -> typing.Any:
    """Helper function to decode a JSON file.

    JSON inputs can contain comments beginning with //.

    Wrapper function for `json.load`, with custom decoder.
    """
    return json.load(stream, cls=JSONWithCommentsDecoder, **kwargs)
