import re
import settings


def test_app_version_is_pep440_string():
    assert isinstance(settings.APP_VERSION, str)
    # simple major.minor.patch (PEP440 subset we use)
    assert re.fullmatch(r"\d+\.\d+\.\d+", settings.APP_VERSION), settings.APP_VERSION
