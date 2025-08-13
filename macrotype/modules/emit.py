from __future__ import annotations

from .scanner import ModuleInfo
from ..types.emit import EmitCtx, emit_top
from .symbols import AliasSymbol, ClassSymbol, FuncSymbol, Symbol, VarSymbol

INDENT = "    "


def emit_module(mi: ModuleInfo) -> list[str]:
    """Format *mi* into ``.pyi`` lines.

    This is a light wrapper around :func:`emit` that walks the ``ModuleInfo``
    tree and formats each symbol.  It is intentionally dumb: no validation or
    reordering occurs here; we simply preserve the structure that earlier passes
    produced while collecting required ``typing`` imports via :class:`EmitCtx`.
    """

    ctx = EmitCtx()
    body: list[str] = []
    for sym in mi.symbols:
        body.extend(_emit_symbol(sym, ctx, indent=0))
        body.append("")
    if body and body[-1] == "":
        body.pop()

    pre: list[str] = []
    if ctx.typing_needed:
        names = ", ".join(sorted(ctx.typing_needed))
        pre.append(f"from typing import {names}")
        if body:
            pre.append("")
    return pre + body


def _emit_symbol(sym: Symbol, ctx: EmitCtx, *, indent: int) -> list[str]:
    pad = INDENT * indent
    match sym:
        case VarSymbol(site=site):
            ty = emit_top(site.ty, ctx)
            return [f"{pad}{sym.name}: {ty}"]
        case AliasSymbol(value=site):
            ty = emit_top(site.ty, ctx)
            return [f"{pad}type {sym.name} = {ty}"]
        case FuncSymbol(params=params, ret=ret, decorators=decos):
            pieces: list[str] = []
            for d in decos:
                pieces.append(f"{pad}@{d}")
            params_s: list[str] = []
            for p in params:
                ann = emit_top(p.ty, ctx)
                params_s.append(f"{p.name}: {ann}")
            param_str = ", ".join(params_s)
            ret_str = f" -> {emit_top(ret.ty, ctx)}" if ret else ""
            pieces.append(f"{pad}def {sym.name}({param_str}){ret_str}: ...")
            return pieces
        case ClassSymbol(bases=bases, td_fields=fields, members=members):
            base_str = ""
            if bases:
                base_str = f"({', '.join(emit_top(b.ty, ctx) for b in bases)})"
            lines = [f"{pad}class {sym.name}{base_str}:"]
            if fields:
                for f in fields:
                    ty = emit_top(f.ty, ctx)
                    lines.append(f"{pad}{INDENT}{f.name}: {ty}")
            if members:
                for m in members:
                    lines.extend(_emit_symbol(m, ctx, indent=indent + 1))
            if not fields and not members:
                lines.append(f"{pad}{INDENT}...")
            return lines
        case _:
            raise NotImplementedError(f"Unsupported symbol: {type(sym).__name__}")
