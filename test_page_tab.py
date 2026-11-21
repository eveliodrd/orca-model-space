#!/usr/bin/env python3
"""The top-bar tab is registered beside the window, and talks through post_message.

Runs without OrcaSlicer: a stub `orca` module carries both capability bases, and
the search adapter is replaced, so this makes no network calls.
"""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

orca_stub = types.ModuleType("orca")


class _CapabilityBase:
    def get_config(self):
        return "{}"


class _PageBase(_CapabilityBase):
    def __init__(self):
        self.posted = []

    def post_message(self, msg):
        self.posted.append(msg)


registered = []
orca_stub.script = types.SimpleNamespace(ScriptPluginCapabilityBase=_CapabilityBase)
orca_stub.pages = types.SimpleNamespace(PagesPluginCapabilityBase=_PageBase)
orca_stub.base = object
orca_stub.plugin = lambda cls: cls
orca_stub.register_capability = registered.append
requested = []
orca_stub.request_permissions = lambda **kw: requested.append(kw)
orca_stub.ExecutionResult = types.SimpleNamespace(success=lambda: None)
orca_stub.host = types.SimpleNamespace(ui=types.SimpleNamespace(create_window=None))
sys.modules["orca"] = orca_stub

import search_engine as se

se.SearchEnginePlugin().register_capabilities()
assert registered == [se.SearchEngineScript, se.SearchEnginePage], registered

# Without a network grant the audit hook refuses every connection.
assert len(requested) == 1 and requested[0]["threading"] is True, requested
assert "https://api-models.snapmaker.com" in requested[0]["network_http"], requested

blocked = RuntimeError("HTTPSConnectionPool(host='api-models.snapmaker.com', port=443): "
                       "... without permission: audit permission required")
assert "https://api-models.snapmaker.com" in se._explain(blocked), se._explain(blocked)

page = se.SearchEnginePage()
assert page.get_name() == "Model Search"
assert page.get_ui() is se.PAGE


class _Fake:
    PLATFORM = "Snapmaker Space"

    @staticmethod
    def enabled(tokens):
        return True

    @staticmethod
    def search(query, tokens):
        return [{"name": query, "platform": "Snapmaker Space"}]


se._SEARCHERS["snapmaker"] = _Fake
page._do_search({"query": "u1", "platforms": ["snapmaker"]})
assert page.posted == [{"action": "results", "results": [
    {"name": "u1", "platform": "Snapmaker Space", "importable": False}]}], page.posted

print("page tab: OK")
