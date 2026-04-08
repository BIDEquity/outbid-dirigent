"""Tests for the spec compactor."""

from unittest.mock import patch, MagicMock

from outbid_dirigent.spec_compactor import (
    CompactMeta,
    CompactSpec,
    Entity,
    EntityField,
    Flow,
    FlowStep,
    GlossaryTerm,
    Requirement,
    compact_spec,
)


class _FakeUsage:
    input_tokens = 1000
    output_tokens = 500
    cache_read_input_tokens = 0
    cache_creation_input_tokens = 0


class _FakeResponse:
    def __init__(self, compact):
        self.parsed_output = compact
        self.usage = _FakeUsage()


def _fixture_compact() -> CompactSpec:
    return CompactSpec(
        meta=CompactMeta(
            title="Test Feature",
            scope="Build a thing.",
            out_of_scope=["Mobile app"],
        ),
        glossary=[
            GlossaryTerm(name="EStE", definition="Einkommensteuer."),
            GlossaryTerm(name="LIQID", definition="German wealth manager."),
        ],
        requirements=[
            Requirement(id="R1", category="auth", priority="must", text="Use Clerk for auth."),
            Requirement(id="R2", category="ui", priority="must", text="Show year banner."),
            Requirement(id="R3", category="data-model", priority="must", text="Entity has name."),
        ],
        entities=[
            Entity(
                name="Entity",
                fields=[
                    EntityField(name="id", type="String", required=True),
                    EntityField(name="name", type="String", required=True),
                ],
            ),
        ],
        flows=[
            Flow(
                name="Auth Flow",
                steps=[
                    FlowStep(n=1, action="User signs in."),
                    FlowStep(n=2, action="Session issued."),
                ],
            ),
        ],
    )


@patch("outbid_dirigent.spec_compactor.anthropic.Anthropic")
def test_returns_compact_spec(mock_cls):
    fixture = _fixture_compact()
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _FakeResponse(fixture)
    mock_cls.return_value = mock_client

    result = compact_spec("# Spec\n\nBuild a thing.")

    assert result is not None
    assert result.meta.title == "Test Feature"
    assert len(result.requirements) == 3
    assert result.requirements[0].id == "R1"

    call_kwargs = mock_client.messages.parse.call_args.kwargs
    assert call_kwargs["output_format"] is CompactSpec


@patch("outbid_dirigent.spec_compactor.anthropic.Anthropic")
def test_returns_none_on_api_error(mock_cls):
    import anthropic

    mock_client = MagicMock()
    mock_client.messages.parse.side_effect = anthropic.APIError(
        message="rate limited",
        request=MagicMock(),
        body=None,
    )
    mock_cls.return_value = mock_client

    result = compact_spec("Some spec")
    assert result is None


@patch("outbid_dirigent.spec_compactor.anthropic.Anthropic")
def test_returns_none_on_refusal(mock_cls):
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _FakeResponse(None)
    mock_cls.return_value = mock_client

    result = compact_spec("Some spec")
    assert result is None


@patch("outbid_dirigent.spec_compactor.anthropic.Anthropic")
def test_saves_to_dirigent_dir(mock_cls, tmp_path):
    fixture = _fixture_compact()
    mock_client = MagicMock()
    mock_client.messages.parse.return_value = _FakeResponse(fixture)
    mock_cls.return_value = mock_client

    compact_spec("Some spec", dirigent_dir=tmp_path)

    saved = tmp_path / "SPEC.compact.json"
    assert saved.exists()

    # Round-trip through Pydantic
    loaded = CompactSpec.model_validate_json(saved.read_text(encoding="utf-8"))
    assert loaded.meta.title == "Test Feature"
    assert len(loaded.requirements) == 3
    assert loaded.glossary[0].name == "EStE"


def test_render_xml_full():
    compact = _fixture_compact()
    xml = compact.render_xml()

    # All reqs present
    assert 'id="R1"' in xml
    assert 'id="R2"' in xml
    assert 'id="R3"' in xml

    # Glossary present
    assert 'name="EStE"' in xml
    assert 'name="LIQID"' in xml

    # Entities present
    assert 'name="Entity"' in xml
    assert 'name="id"' in xml

    # Flows present
    assert 'name="Auth Flow"' in xml
    assert "User signs in." in xml

    # Meta
    assert "<title>Test Feature</title>" in xml
    assert "<item>Mobile app</item>" in xml


def test_render_xml_filtered_reqs():
    compact = _fixture_compact()
    xml = compact.render_xml(only_req_ids={"R1", "R3"})

    # Only R1 and R3 present, R2 dropped
    assert 'id="R1"' in xml
    assert 'id="R3"' in xml
    assert 'id="R2"' not in xml

    # Glossary, entities, flows still in full
    assert 'name="EStE"' in xml
    assert 'name="LIQID"' in xml
    assert 'name="Entity"' in xml
    assert 'name="Auth Flow"' in xml


def test_render_xml_includes_flows_hint():
    compact = _fixture_compact()
    xml = compact.render_xml()
    assert "DO NOT implement all flows" in xml


def test_render_xml_includes_entities_hint():
    compact = _fixture_compact()
    xml = compact.render_xml()
    assert "implement only what your task requires" in xml


def test_render_xml_must_satisfy_block():
    compact = _fixture_compact()
    xml = compact.render_xml(only_req_ids={"R1"})
    assert "<must-satisfy" in xml
    assert "YOUR task must address" in xml


def test_render_xml_empty_filter_drops_must_satisfy():
    compact = _fixture_compact()
    xml = compact.render_xml(only_req_ids=set())
    # No matching reqs → no must-satisfy block
    assert "<must-satisfy" not in xml
    # But glossary still present
    assert 'name="EStE"' in xml


def test_render_xml_escapes_special_chars():
    compact = CompactSpec(
        meta=CompactMeta(title="X & Y", scope="A < B"),
        requirements=[
            Requirement(id="R1", category="ui", priority="must", text='Use "quotes" & <tags>'),
        ],
    )
    xml = compact.render_xml()
    assert "X &amp; Y" in xml
    assert "A &lt; B" in xml
    assert "&quot;quotes&quot;" in xml
    assert "&amp; &lt;tags&gt;" in xml


def test_pydantic_round_trip(tmp_path):
    fixture = _fixture_compact()
    path = tmp_path / "compact.json"
    path.write_text(fixture.model_dump_json(indent=2), encoding="utf-8")

    loaded = CompactSpec.model_validate_json(path.read_text(encoding="utf-8"))
    assert loaded == fixture
