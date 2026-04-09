"""Tests for the LLM route discriminator."""

from unittest.mock import patch, MagicMock

import pytest

from outbid_dirigent.llm_router import (
    RouteChoice,
    RouteDecision,
    determine_route_llm,
    ROUTE_SYSTEM_PROMPT,
)


class _FakeUsage:
    input_tokens = 100
    output_tokens = 50
    cache_read_input_tokens = 0
    cache_creation_input_tokens = 0


class _FakeResponse:
    def __init__(self, decision):
        self.parsed_output = decision
        self.usage = _FakeUsage()


@patch("outbid_dirigent.llm_router.anthropic.Anthropic")
def test_returns_route_decision(mock_cls):
    decision = RouteDecision(
        route=RouteChoice.HYBRID,
        justification="Feature on existing project",
        confidence="high",
    )
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _FakeResponse(decision)
    mock_cls.return_value = mock_client

    result = determine_route_llm("Add a login page", commit_count=150)

    assert result is not None
    assert result.route == RouteChoice.HYBRID
    assert result.confidence == "high"
    assert "existing project" in result.justification

    # Verify parse was called with structured output
    call_kwargs = mock_client.messages.parse.call_args.kwargs
    assert call_kwargs["output_format"] is RouteDecision
    assert call_kwargs["system"] == ROUTE_SYSTEM_PROMPT


@patch("outbid_dirigent.llm_router.anthropic.Anthropic")
def test_passes_test_harness_summary(mock_cls):
    decision = RouteDecision(
        route=RouteChoice.QUICK,
        justification="Small fix",
        confidence="high",
    )
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _FakeResponse(decision)
    mock_cls.return_value = mock_client

    determine_route_llm(
        "Fix typo in header",
        commit_count=50,
        test_harness_summary="Base URL: http://localhost:3000\nAuth: none",
    )

    user_content = mock_client.messages.parse.call_args.kwargs["messages"][0]["content"]
    assert "localhost:3000" in user_content


@patch("outbid_dirigent.llm_router.anthropic.Anthropic")
def test_returns_none_on_api_error(mock_cls):
    import anthropic
    mock_client = MagicMock()
    mock_client.messages.parse.side_effect = anthropic.APIError(
        message="rate limited",
        request=MagicMock(),
        body=None,
    )
    mock_cls.return_value = mock_client

    result = determine_route_llm("Some spec", commit_count=10)
    assert result is None


@patch("outbid_dirigent.llm_router.anthropic.Anthropic")
def test_returns_none_on_refusal(mock_cls):
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _FakeResponse(None)
    mock_cls.return_value = mock_client

    result = determine_route_llm("Some spec", commit_count=10)
    assert result is None


@patch("outbid_dirigent.llm_router.anthropic.Anthropic")
def test_saves_decision_to_dirigent_dir(mock_cls, tmp_path):
    decision = RouteDecision(
        route=RouteChoice.LEGACY,
        justification="Migration from Ruby",
        confidence="medium",
    )
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _FakeResponse(decision)
    mock_cls.return_value = mock_client

    determine_route_llm("Migrate auth", commit_count=3000, dirigent_dir=tmp_path)

    llm_route_file = tmp_path / "LLM_ROUTE.json"
    assert llm_route_file.exists()

    import json
    data = json.loads(llm_route_file.read_text())
    assert data["route"] == "legacy"
    assert data["justification"] == "Migration from Ruby"


def test_route_decision_validates_enum():
    """RouteDecision only accepts valid route values."""
    with pytest.raises(ValueError):
        RouteDecision(route="invalid", justification="x", confidence="high")


def test_all_routes_in_choice_enum():
    """All routes the router knows must be in RouteChoice."""
    from outbid_dirigent.router import RouteType
    for rt in RouteType:
        assert rt.value in [rc.value for rc in RouteChoice], f"{rt.value} missing from RouteChoice"
