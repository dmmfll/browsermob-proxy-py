import os
import re
import shutil
import sys
from os import environ

import pytest
import selenium.webdriver.common.desired_capabilities
from browsermobproxy.client import Client
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options

COMMAND_EXECUTOR = "http://172.17.0.1:4444/wd/hub"


class TestRemote:
    def setup_class(self):
        firefox_binary = shutil.which("firefox")
        if firefox_binary is None:
            raise RuntimeError("No firefox executable found.")

        self.client = Client("localhost:9090")
        options = Options()
        options.binary_location = firefox_binary
        options.add_argument("network.proxy.allow_hijacking_localhost=true")

        # Include proxy values manually.
        # The selenium_proxy method returns values for sslProxy which
        # fail in Firefox.
        proxy = Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = self.client.proxy

        # Allow proxying of localhost addresses.
        # https://stackoverflow.com/a/57419409/1913726
        firefox_profile = FirefoxProfile()
        firefox_profile.set_preference("network.proxy.allow_hijacking_localhost", True)

        self.driver = webdriver.Remote(
            command_executor=COMMAND_EXECUTOR,
            browser_profile=firefox_profile,
            proxy=proxy,
            options=options,
        )
        targetURL = "http://localhost:8000/versions.js"
        pattern = r"http:\/\/localhost:8000\/versions\.[a-z]+$"
        pattern_ = re.compile(pattern)
        match = pattern_.match(targetURL)
        assert match.group() == targetURL
        self.pattern = pattern
        self.canonical_url = "http://localhost:8000/versions.json"
        self.targetURL = targetURL

    def teardown_class(self):
        self.client.close()
        self.driver.quit()

    @pytest.mark.human
    def test_set_clear_url_rewrite_rule(self):

        needle = "Makayla Thomas"
        self.driver.get(self.canonical_url)
        assert needle in self.driver.page_source

        response = self.client.rewrite_url(self.pattern, self.canonical_url)
        assert 200 == response
        self.driver.get(self.targetURL)
        assert needle in self.driver.page_source

        assert self.client.clear_all_rewrite_url_rules() == 200
        self.driver.get(self.targetURL)
        assert "needle" not in self.driver.page_source

    @pytest.mark.human
    def test_response_interceptor(self):
        content = "Response successfully intercepted."
        self.targetURL = f"{self.canonical_url}?hello"
        self.client.response_interceptor(
            """if(messageInfo.getOriginalUrl().contains('?hello')){contents.setTextContents("%s");}"""
            % content
        )
        self.driver.get(self.targetURL)
        assert content in self.driver.page_source
