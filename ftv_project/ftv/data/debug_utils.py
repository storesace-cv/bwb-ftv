# Fase 3 — utilitários de debug (opcional)
import functools, traceback, sys, time

def log_call(fn):
    """Decorator que loga entrada/saída e erros com contexto (args, tempo de execução)."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        fname = f"{fn.__module__}.{fn.__qualname__}"
        print(f"[DEBUG] ➜ {fname} args={args[1:] if len(args)>1 else []} kwargs={kwargs}")
        try:
            out = fn(*args, **kwargs)
            dt = (time.time() - t0) * 1000
            print(f"[DEBUG] ✓ {fname} -> {type(out).__name__} em {dt:.1f}ms")
            return out
        except Exception as e:
            dt = (time.time() - t0) * 1000
            print(f"[DEBUG][ERRO] ✗ {fname} falhou em {dt:.1f}ms: {e}", file=sys.stderr)
            traceback.print_exc()
            raise
    return wrapper