import pytest
import threading
from flask import Flask, redirect
from metagpt.config import CONFIG
from metagpt.tools import web_browser_engine_playwright

# Flask 리다이렉션 서버 정의
app = Flask(__name__)


@app.route("/")
def home():
    return redirect("/redirected")


@app.route("/redirected")
def redirected():
    return "You have been redirected."


# 별도의 스레드에서 Flask 서버 실행
def run_flask_app():
    app.run(port=5000)


flask_thread = threading.Thread(target=run_flask_app)
flask_thread.start()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "browser_type, use_proxy, kwagrs, url, urls",
    [
        ("chromium", {"proxy": True}, {}, "https://fuzhi.ai", ("https://fuzhi.ai",)),
        ("firefox", {}, {"ignore_https_errors": True}, "https://fuzhi.ai", ("https://fuzhi.ai",)),
        ("webkit", {}, {"ignore_https_errors": True}, "https://fuzhi.ai", ("https://fuzhi.ai",)),
        ("chromium", False, {}, "http://localhost:5000", "http://localhost:5000/redirected"),
        ("firefox", False, {}, "http://localhost:5000", "http://localhost:5000/redirected"),
        ("webkit", False, {}, "http://localhost:5000", "http://localhost:5000/redirected"),
    ],
    ids=[
        "chromium-normal",
        "firefox-normal",
        "webkit-normal",
        "chromium-redirect",
        "firefox-redirect",
        "webkit-redirect",
    ],
)
async def test_scrape_web_page(browser_type, use_proxy, kwagrs, url, urls, proxy, capfd):
    try:
        global_proxy = CONFIG.global_proxy
        if use_proxy:
            CONFIG.global_proxy = proxy
        browser = web_browser_engine_playwright.PlaywrightWrapper(browser_type, **kwagrs)
        result = await browser.run(url)
        result = result.inner_text
        assert isinstance(result, str)
        assert "Deepwisdom" in result
        if urls:
            results = await browser.run(url, *urls)
            assert isinstance(results, list)
            assert len(results) == len(urls) + 1
            assert all(("Deepwisdom" in i) for i in results)
        if use_proxy:
            assert "Proxy:" in capfd.readouterr().out
    finally:
        CONFIG.global_proxy = global_proxy
