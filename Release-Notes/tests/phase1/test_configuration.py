"""Tests for the Phase 1 source configuration."""

from app.configuration import (
    DEFAULT_CONFIG_PATH,
    enabled_sources,
    load_configuration,
)


def test_project_configuration_loads():
    configuration = load_configuration(DEFAULT_CONFIG_PATH)

    github = configuration["sources"]["github"]

    assert github["enabled"] is True
    assert (
        github["repository"]
        == "chrisjohn83/SmartTouch-Cloud-Platform"
    )
    assert github["base_branch"] == "main"


def test_enabled_sources_excludes_disabled_sources():
    configuration = load_configuration(DEFAULT_CONFIG_PATH)

    sources = enabled_sources(configuration)

    assert "github" in sources
    assert "jira" not in sources
    assert "confluence" not in sources
    assert "bitbucket" not in sources
