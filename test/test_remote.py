import os
import shutil
import sys
from os import environ
from random import choice, randint
from string import ascii_lowercase
from urllib.parse import urlunsplit

import pytest
import selenium.webdriver.common.desired_capabilities
from selenium import webdriver

COMMAND_EXECUTOR = "http://172.17.0.1:4444/wd/hub"


def setup_module(module):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestRemote(object):
    def setup_method(self, method):
        from browsermobproxy.client import Client
        from selenium.webdriver.common.proxy import Proxy, ProxyType
        from selenium.webdriver.firefox.options import Options

        firefox_binary = shutil.which("firefox")
        if firefox_binary is None:
            raise RuntimeError("No firefox executable found.")
        self.client = Client("localhost:9090")
        options = Options()
        options.binary_location = firefox_binary

        proxy = Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = self.client.proxy

        self.driver = webdriver.Remote(
            command_executor=COMMAND_EXECUTOR, options=options, proxy=proxy
        )

    def teardown_method(self, method):
        self.client.close()
        self.driver.quit()

    @pytest.mark.human
    def test_set_clear_url_rewrite_rule(self):
        """Assume HTTP server running on localhost with a document
        named 000.html"""

        query__fragment = ("",) * 2
        tokens = scheme, netloc, path, query, fragment = (
            "http",
            "localhost:8000",
            "000.html",
            *query__fragment,
        )
        canonical_url = urlunsplit(tokens)
        random_word = "".join((choice(ascii_lowercase) for _ in range(randint(1, 10))))
        target_url = urlunsplit(
            (scheme, netloc, f"{random_word}.html", *query__fragment)
        )
        needle = "64796c38a7f54d5ab735cdadd575a9ca"
        self.driver.get(canonical_url)
        assert needle in self.driver.page_source

        assert 200 == self.client.rewrite_url(
            r"[a-z]+\.html$",
            path,
        )
        self.driver.get(target_url)
        assert needle in self.driver.page_source
        assert self.client.clear_all_rewrite_url_rules() == 200
        self.driver.get(rewrite_url)
        assert needle not in self.driver.page_source

    @pytest.mark.human
    def test_response_interceptor(self):
        content = "Response successfully intercepted"
        target_url = "https://saucelabs.com/versions.json?hello"
        self.client.response_interceptor(
            """if(messageInfo.getOriginalUrl().contains('?hello')){contents.setTextContents("%s");}"""
            % content
        )
        self.driver.get(target_url)
        assert content in self.driver.page_source
