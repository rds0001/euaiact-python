"""Linux-Prüfwerkzeug: Kindprozess ohne neue Netzwerk-Sockets ausführen.

Kein Bestandteil der Libraries. seccomp wird vor exec geladen und vererbt.
"""

import ctypes
import ctypes.util
import errno
import os
import sys


def sperren():
    pfad = ctypes.util.find_library("seccomp")
    if not pfad:
        raise RuntimeError("libseccomp für den Betriebssystem-Nachweis erforderlich")
    bibliothek = ctypes.CDLL(pfad, use_errno=True)
    bibliothek.seccomp_init.argtypes = [ctypes.c_uint32]
    bibliothek.seccomp_init.restype = ctypes.c_void_p
    bibliothek.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    bibliothek.seccomp_syscall_resolve_name.restype = ctypes.c_int
    bibliothek.seccomp_rule_add.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    bibliothek.seccomp_rule_add.restype = ctypes.c_int
    bibliothek.seccomp_load.argtypes = [ctypes.c_void_p]
    bibliothek.seccomp_load.restype = ctypes.c_int
    bibliothek.seccomp_release.argtypes = [ctypes.c_void_p]
    kontext = bibliothek.seccomp_init(0x7FFF0000)
    if not kontext:
        raise RuntimeError("seccomp-Kontext konnte nicht erzeugt werden")
    try:
        for name in (
            b"socket",
            b"socketpair",
            b"connect",
            b"sendto",
            b"sendmsg",
            b"sendmmsg",
        ):
            nummer = bibliothek.seccomp_syscall_resolve_name(name)
            if (
                nummer < 0
                or bibliothek.seccomp_rule_add(
                    kontext, 0x00050000 | errno.EPERM, nummer, 0
                )
                != 0
            ):
                raise RuntimeError(
                    "Netzsperre konnte nicht vollständig eingerichtet werden"
                )
        if bibliothek.seccomp_load(kontext) != 0:
            raise RuntimeError("Netzsperre konnte nicht aktiviert werden")
    finally:
        bibliothek.seccomp_release(kontext)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Aufruf: netzsperre.py PROGRAMM ARGUMENTE ...")
    sperren()
    os.execvp(sys.argv[1], sys.argv[1:])
