from hypothesis import settings


def pytest_configure():
    print("Running test config now")

    settings.register_profile("ci", derandomize=True)
    settings.load_profile("ci")
