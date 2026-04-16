"""
Tests for URL encoding of repo names that contain slashes (e.g. "build/buildkit-test").

The registry API requires slashes in repository names to be percent-encoded (%2F),
otherwise the API interprets extra path segments as part of the route and returns
{"error":"failed to list manifests"} or 0 images.

Correct:   /repositories/build%2Fbuildkit-test/images
Incorrect: /repositories/build/buildkit-test/images
"""
import os
import pytest

from config.logger_config import setup_logging
from clients.cleanup_repository import get_images, delete_image

setup_logging()

BASE_URL = "https://cr.selcloud.ru/api/v1"
REGISTRY_ID = "9975a430-0fd7-4ceb-a1c4-0e73a403ab57"
TOKEN = "test-token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = body if body is not None else []
        self.text = str(self._body)

    def json(self):
        return self._body

    def raise_for_status(self):
        pass


class FakeSession:
    """Records the last URL used for GET / DELETE calls."""

    def __init__(self, response: FakeResponse):
        self._response = response
        self.last_get_url: str | None = None
        self.last_delete_url: str | None = None

    def get(self, url, headers=None, timeout=None):
        self.last_get_url = url
        return self._response

    def delete(self, url, headers=None, timeout=None):
        self.last_delete_url = url
        return self._response


# ---------------------------------------------------------------------------
# get_images — simple repo name (no slash)
# ---------------------------------------------------------------------------

def test_get_images_simple_repo_url():
    """Simple repo name must not be altered."""
    session = FakeSession(FakeResponse(200, []))
    get_images(session, BASE_URL, REGISTRY_ID, TOKEN, "myapp")

    expected = f"{BASE_URL}/registries/{REGISTRY_ID}/repositories/myapp/images"
    assert session.last_get_url == expected


# ---------------------------------------------------------------------------
# get_images — repo name with slash
# ---------------------------------------------------------------------------

def test_get_images_slash_repo_url_encoded():
    """Slash in repo name must be percent-encoded as %2F."""
    session = FakeSession(FakeResponse(200, []))
    get_images(session, BASE_URL, REGISTRY_ID, TOKEN, "build/buildkit-test")

    expected = f"{BASE_URL}/registries/{REGISTRY_ID}/repositories/build%2Fbuildkit-test/images"
    assert session.last_get_url == expected


def test_get_images_slash_repo_url_not_raw_slash():
    """Raw slash in the URL path must not appear for nested repo names."""
    session = FakeSession(FakeResponse(200, []))
    get_images(session, BASE_URL, REGISTRY_ID, TOKEN, "build/buildkit-test")

    # The URL must not contain a raw slash between 'repositories/' and '/images'
    # i.e. it must not look like /repositories/build/buildkit-test/images
    suffix_after_repositories = session.last_get_url.split("/repositories/", 1)[1]
    assert suffix_after_repositories.startswith("build%2F"), (
        f"Expected URL-encoded repo segment, got: {session.last_get_url}"
    )


def test_get_images_double_slash_repo_url_encoded():
    """Deeply nested names (two slashes) must both be encoded."""
    session = FakeSession(FakeResponse(200, []))
    get_images(session, BASE_URL, REGISTRY_ID, TOKEN, "a/b/c")

    expected = f"{BASE_URL}/registries/{REGISTRY_ID}/repositories/a%2Fb%2Fc/images"
    assert session.last_get_url == expected


def test_get_images_cache_repo_url_encoded():
    """Cache-variant repo names with slash must also be encoded."""
    session = FakeSession(FakeResponse(200, []))
    get_images(session, BASE_URL, REGISTRY_ID, TOKEN, "build/buildkit-test-cache")

    expected = (
        f"{BASE_URL}/registries/{REGISTRY_ID}/repositories/build%2Fbuildkit-test-cache/images"
    )
    assert session.last_get_url == expected


# ---------------------------------------------------------------------------
# delete_image — repo name with slash
# ---------------------------------------------------------------------------

def test_delete_image_simple_repo_url():
    """Simple repo name must not be altered in delete URL."""
    session = FakeSession(FakeResponse(204))
    delete_image(session, BASE_URL, REGISTRY_ID, TOKEN, "myapp", "sha256:abc", dry_run=False)

    expected = f"{BASE_URL}/registries/{REGISTRY_ID}/repositories/myapp/sha256:abc"
    assert session.last_delete_url == expected


def test_delete_image_slash_repo_url_encoded():
    """Slash in repo name must be percent-encoded in delete URL."""
    session = FakeSession(FakeResponse(204))
    delete_image(
        session, BASE_URL, REGISTRY_ID, TOKEN,
        "build/buildkit-test", "sha256:deadbeef", dry_run=False
    )

    expected = (
        f"{BASE_URL}/registries/{REGISTRY_ID}/repositories/build%2Fbuildkit-test/sha256:deadbeef"
    )
    assert session.last_delete_url == expected


def test_delete_image_dry_run_does_not_call_api():
    """dry_run=True must not issue any HTTP DELETE request."""
    session = FakeSession(FakeResponse(204))
    delete_image(
        session, BASE_URL, REGISTRY_ID, TOKEN,
        "build/buildkit-test", "sha256:deadbeef", dry_run=True
    )

    assert session.last_delete_url is None
