"""Temporary headless rendering of the decorative Hero."""

import re
import asyncio
import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
from main import app

directory = Path(tempfile.mkdtemp(prefix="orbi-hero-"))
html = app.test_client().get("/").get_data(as_text=True)
html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S)
css = (root / "src/static/style.css").read_text(encoding="utf-8")
html = re.sub(r"<link\b[^>]*>", lambda _: "<style>" + css + "</style>", html)
preview = directory / "hero.html"
preview.write_text(html, encoding="utf-8")
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
profile = directory / "browser-profile"
process = subprocess.Popen([
    chrome, "--headless", "--hide-scrollbars", "--no-first-run",
    "--remote-debugging-port=0", "--user-data-dir=" + str(profile), "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW)


async def render():
    active_port = profile / "DevToolsActivePort"
    for _ in range(100):
        if active_port.exists():
            break
        await asyncio.sleep(0.1)
    port = active_port.read_text().splitlines()[0]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f"http://127.0.0.1:{port}/json/list", timeout=5) as response:
        target = json.load(response)[0]
    async with websockets.connect(target["webSocketDebuggerUrl"]) as connection:
        sequence = 0

        async def call(method, params=None):
            nonlocal sequence
            sequence += 1
            await connection.send(json.dumps({
                "id": sequence, "method": method, "params": params or {},
            }))
            while True:
                result = json.loads(await asyncio.wait_for(connection.recv(), 5))
                if result.get("id") == sequence:
                    return result.get("result", {})

        for name, width in [("desktop", 1365), ("mobile", 390)]:
            await call("Emulation.setDeviceMetricsOverride", {
                "width": width, "height": 1000, "deviceScaleFactor": 1,
                "mobile": name == "mobile",
            })
            await call("Page.navigate", {"url": preview.as_uri()})
            await asyncio.sleep(1)
            result = await call("Runtime.evaluate", {
                "expression": "JSON.stringify({viewport:innerWidth,content:document.documentElement.scrollWidth,hero:document.querySelector('.hero').getBoundingClientRect().toJSON(),chip:document.querySelector('.ai-chip-frame').getBoundingClientRect().toJSON(),animation:getComputedStyle(document.querySelector('.ai-chip')).animationName})",
                "returnByValue": True,
            })
            print(name, result, flush=True)
        await call("Emulation.setEmulatedMedia", {
            "features": [{"name": "prefers-reduced-motion", "value": "reduce"}],
        })
        print(await call("Runtime.evaluate", {
            "expression": "getComputedStyle(document.querySelector('.ai-chip')).animationName",
            "returnByValue": True,
        }), flush=True)


try:
    asyncio.run(asyncio.wait_for(render(), 25))
finally:
    process.terminate()
    process.wait(timeout=10)
