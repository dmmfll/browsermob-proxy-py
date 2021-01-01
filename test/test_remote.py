import os
import shutil
import sys
from os import environ

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
        import re

        targetURL = "http://localhost:8000/versions.js"
        pattern = r"http:\/\/localhost:8000\/versions\.[a-z]+$"
        pattern_ = re.compile(pattern)
        match = pattern_.match(targetURL)
        assert match.group() == targetURL
        canonical_url = "http://localhost:8000/versions.json"
        needle = "Makayla Thomas"
        self.driver.get(canonical_url)
        assert needle in self.driver.page_source

        response = self.client.rewrite_url(pattern, canonical_url)
        assert 200 == response
        self.driver.get(targetURL)
        assert needle in self.driver.page_source

        assert self.client.clear_all_rewrite_url_rules() == 200
        self.driver.get(targetURL)
        assert "needle" not in self.driver.page_source

    @pytest.mark.human
    def test_response_interceptor(self):
        content = "Response successfully intercepted"
        targetURL = "https://saucelabs.com/versions.json?hello"
        self.client.response_interceptor(
            """if(messageInfo.getOriginalUrl().contains('?hello')){contents.setTextContents("%s");}"""
            % content
        )
        self.driver.get(targetURL)
        assert content in self.driver.page_source
