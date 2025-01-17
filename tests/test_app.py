from flask import current_app

from se.app import create_app


class TestApp:
    def setup_method(self) -> None:
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown_method(self) -> None:
        self.app_context.pop()

    def test_app_exist(self) -> None:
        assert current_app is not None

    def test_app_is_testing(self):
        assert current_app.config["TESTING"]
