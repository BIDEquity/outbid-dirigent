"""Tests for the idempotent ship() behaviour.

The bug: re-running ship() in the same workspace (resume, manual re-trigger)
used to produce a timestamp-suffixed branch like ``dirigent/foo-20260501...``
in addition to the original ``dirigent/foo``, which created a *new* PR for
the same FR. Expected behaviour: same FR ⇒ same branch ⇒ same PR; re-runs
update the existing PR.
"""

from pathlib import Path
from typing import Any, List
from unittest.mock import MagicMock, patch

import pytest

from outbid_dirigent.shipper import Shipper


def _ok(stdout: str = "") -> MagicMock:
    return MagicMock(returncode=0, stdout=stdout, stderr="")


def _err(stderr: str = "boom", returncode: int = 1) -> MagicMock:
    return MagicMock(returncode=returncode, stdout="", stderr=stderr)


@pytest.fixture
def shipper(tmp_path: Path) -> Shipper:
    plan = MagicMock(title="Test Feature")
    s = Shipper(repo_path=tmp_path, plan=plan, dry_run=False)
    s._generate_pr_body = MagicMock(return_value="body")  # type: ignore[method-assign]
    s._strip_artifacts = MagicMock()  # type: ignore[method-assign]
    s._resolve_base_branch = MagicMock(return_value="master")  # type: ignore[method-assign]
    return s


def _capture_call(run_mock: MagicMock, *match_argv: str) -> List[str]:
    """Find the most recent subprocess.run call that starts with ``match_argv``."""
    for call in reversed(run_mock.call_args_list):
        argv = call.args[0] if call.args else call.kwargs.get("args", [])
        if list(argv[: len(match_argv)]) == list(match_argv):
            return list(argv)
    raise AssertionError(
        f"No subprocess.run call starting with {match_argv!r}. "
        f"Calls: {[c.args[0] if c.args else c.kwargs.get('args') for c in run_mock.call_args_list]}"
    )


def _has_call(run_mock: MagicMock, *match_argv: str) -> bool:
    for call in run_mock.call_args_list:
        argv = call.args[0] if call.args else call.kwargs.get("args", [])
        if list(argv[: len(match_argv)]) == list(match_argv):
            return True
    return False


# ─── Re-run scenarios ────────────────────────────────────────────────────────


def test_first_run_does_not_force_push(shipper: Shipper) -> None:
    """Plain first run: no local branch, push works fast-forward, plain
    ``git push`` (without --force). No reason to clobber anything."""

    def side_effect(argv: List[str], **_: Any) -> MagicMock:
        # Branch does NOT exist locally on first run.
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return _err("not a valid ref")
        # Push succeeds first try.
        if argv[:3] == ["git", "push", "-u"]:
            return _ok()
        return _ok("https://github.com/x/y/pull/1")

    with patch(
        "outbid_dirigent.shipper.shutil.which", return_value="/usr/bin/gh"
    ), patch("outbid_dirigent.shipper.subprocess.run", side_effect=side_effect) as run_mock:
        assert shipper.ship() is True

    push = _capture_call(run_mock, "git", "push", "-u")
    assert "--force" not in push, f"--force should not appear on first-run push, got: {push}"
    # No timestamp suffix — plain dirigent/<slug>.
    assert shipper.branch_name == "dirigent/test-feature"


def test_rerun_drops_local_branch_and_force_pushes(shipper: Shipper) -> None:
    """Re-run in the same workspace: local branch exists, gets recreated;
    push retries with --force when origin already has the previous run's
    commits."""

    state = {"first_push": True}

    def side_effect(argv: List[str], **_: Any) -> MagicMock:
        # Branch exists locally (previous run left it).
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return _ok()
        # First push gets rejected non-FF; second push with --force succeeds.
        if argv[:3] == ["git", "push", "-u"]:
            if "--force" in argv:
                return _ok()
            if state["first_push"]:
                state["first_push"] = False
                return _err("! [rejected] dirigent/test-feature -> dirigent/test-feature (non-fast-forward)")
            return _ok()
        # gh pr create succeeds on this branch — typical when the existing
        # PR was closed/merged but branch was reused.
        return _ok("https://github.com/x/y/pull/9")

    with patch(
        "outbid_dirigent.shipper.shutil.which", return_value="/usr/bin/gh"
    ), patch("outbid_dirigent.shipper.subprocess.run", side_effect=side_effect) as run_mock:
        assert shipper.ship() is True

    # Detached HEAD + branch -D were called to drop the stale local branch.
    assert _has_call(run_mock, "git", "checkout", "--detach")
    assert _has_call(run_mock, "git", "branch", "-D", "dirigent/test-feature")
    # Force-push retry happened.
    forced = [
        c.args[0]
        for c in run_mock.call_args_list
        if list(c.args[0][:3]) == ["git", "push", "-u"] and "--force" in c.args[0]
    ]
    assert forced, "Expected a force-push retry after non-FF rejection"
    # Branch name stays canonical — no timestamp suffix.
    assert shipper.branch_name == "dirigent/test-feature"


def test_rerun_when_pr_already_exists_reuses_url(shipper: Shipper) -> None:
    """``gh pr create`` rejects re-runs with 'a PR already exists'. Shipper
    should look up the existing PR's URL and surface it as ``self.pr_url``
    instead of leaving the caller in the dark."""

    def side_effect(argv: List[str], **_: Any) -> MagicMock:
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return _ok()  # local branch exists (re-run)
        if argv[:3] == ["git", "push", "-u"]:
            return _ok() if "--force" in argv else _err("non-fast-forward")
        if argv[:3] == ["gh", "pr", "create"]:
            return _err("a pull request for branch ... already exists")
        if argv[:3] == ["gh", "pr", "list"]:
            return _ok('[{"url": "https://github.com/x/y/pull/42"}]')
        return _ok()

    with patch(
        "outbid_dirigent.shipper.shutil.which", return_value="/usr/bin/gh"
    ), patch("outbid_dirigent.shipper.subprocess.run", side_effect=side_effect):
        assert shipper.ship() is True

    assert shipper.pr_url == "https://github.com/x/y/pull/42"


# ─── _lookup_existing_pr_url ────────────────────────────────────────────────


def test_lookup_returns_url_from_gh_output(tmp_path: Path) -> None:
    s = Shipper(repo_path=tmp_path, plan=None, dry_run=False)
    with patch(
        "outbid_dirigent.shipper.subprocess.run",
        return_value=_ok('[{"url": "https://github.com/x/y/pull/7"}]'),
    ):
        assert s._lookup_existing_pr_url("dirigent/foo") == "https://github.com/x/y/pull/7"


def test_lookup_returns_none_when_no_open_pr(tmp_path: Path) -> None:
    s = Shipper(repo_path=tmp_path, plan=None, dry_run=False)
    with patch(
        "outbid_dirigent.shipper.subprocess.run", return_value=_ok("[]")
    ):
        assert s._lookup_existing_pr_url("dirigent/foo") is None


def test_lookup_returns_none_on_gh_error(tmp_path: Path) -> None:
    s = Shipper(repo_path=tmp_path, plan=None, dry_run=False)
    with patch(
        "outbid_dirigent.shipper.subprocess.run", return_value=_err("auth required")
    ):
        assert s._lookup_existing_pr_url("dirigent/foo") is None


def test_lookup_returns_none_on_invalid_json(tmp_path: Path) -> None:
    s = Shipper(repo_path=tmp_path, plan=None, dry_run=False)
    with patch(
        "outbid_dirigent.shipper.subprocess.run", return_value=_ok("not-json")
    ):
        assert s._lookup_existing_pr_url("dirigent/foo") is None


# ─── Push-failure semantics (403, auth, etc.) ───────────────────────────────


def test_push_403_returns_false_and_pushed_stays_false(shipper: Shipper) -> None:
    """A 403 (or any non-divergence push failure) is a real failure: ship()
    must return False and `pushed` must stay False so the executor doesn't
    emit a 'gepusht' success message."""

    def side_effect(argv: List[str], **_: Any) -> MagicMock:
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return _err("not a valid ref")  # first run, no local branch
        if argv[:3] == ["git", "push", "-u"]:
            return _err(
                "remote: Write access to repository not granted.\n"
                "fatal: unable to access ...: The requested URL returned error: 403"
            )
        return _ok()

    with patch(
        "outbid_dirigent.shipper.shutil.which", return_value="/usr/bin/gh"
    ), patch("outbid_dirigent.shipper.subprocess.run", side_effect=side_effect) as run_mock:
        assert shipper.ship() is False

    assert shipper.pushed is False, "pushed must stay False on 403"
    assert shipper.pr_url is None, "no PR should be attempted after a failed push"
    # gh pr create must NOT be invoked when the branch never reached origin.
    assert not _has_call(run_mock, "gh", "pr", "create")
