"""Etapa 8 — Promocion al segundo cerebro: Global Brain (Obsidian).

Delegada en gp.brain: clasifica cada nodo por el principio de Kardashev y
mantiene la boveda completa (inicio, indices, pulso diario y notas atomicas).
"""
from . import brain


def run(pulse: dict, log=print) -> int:
    log("[8/8] Promocion al Global Brain (Obsidian · Kardashev + PARA)")
    return brain.build(pulse, log)
