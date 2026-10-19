"""Versioned switches and cheap observations for the adaptive parameter bots.

This registry deliberately excludes quality gates. Counts describe work, not
causal value; only paired production conversions can establish that value.
"""
from __future__ import annotations

BOT_NAMES = ('reverse_coordinates', 'shuffled_coordinates', 'joint_restart',
             'fine_coordinates', 'geometry_pair', 'color_pair')


def peak_memory_bytes():
    """Worker peak resident memory; includes imports and native renderer memory."""
    import os
    if os.name != 'nt':
        import resource
        import sys
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform == 'darwin' else value*1024)
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [('cb',wintypes.DWORD),('page_faults',wintypes.DWORD)]+[
            (name,ctypes.c_size_t) for name in ('peak_working_set','working_set','peak_paged_pool',
            'paged_pool','peak_nonpaged_pool','nonpaged_pool','pagefile','peak_pagefile')]

    counter = Counters()
    counter.cb = ctypes.sizeof(counter)
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL('psapi',use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counter),counter.cb):
        return None
    return counter.peak_working_set


def registry(disabled=()):
    unknown = set(disabled)-set(BOT_NAMES)
    if unknown:
        raise ValueError('Unknown search components: '+', '.join(sorted(unknown)))
    return [dict(id=name, version=1, requires=['portfolio', 'adaptive'],
                 switch='--disable-search-bot '+name, enabled=name not in disabled)
            for name in BOT_NAMES]


def snapshot(session, config):
    bots = {name: dict(proposals=0, generated=0, cache_hits=0, valid=0,
                       rejected=0, improvements=0, active_seconds=0.) for name in BOT_NAMES}
    for board in session.bot_searches.values():
        for bot in board.bots:
            total = bots[bot.name]
            total['proposals'] += bot.proposals
            for key, value in getattr(bot, 'observation', {}).items():
                total[key] += value
    return dict(schema='search_components_v1', registry=registry(config.get('disabled_bots', ())),
                observation_enabled=config.get('component_observation', True), bots=bots,
                worker_peak_memory_bytes=peak_memory_bytes(),
                blackboards=len(session.bot_searches),
                shared_cache_hits=sum(b.cache_hits for b in session.bot_searches.values()),
                observation_seconds=sum(getattr(b, 'observation_seconds', 0.)
                                        for b in session.bot_searches.values()))
