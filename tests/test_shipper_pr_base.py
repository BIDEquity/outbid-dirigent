"""Tests for Shipper._resolve_base_branch and the ``gh pr create --base`` wiring.

The bug: PRs opened by Shipper had no ``--base`` argument so gh fell back to the
repo default branch (master) even when the workspace was cloned from a different
branch (e.g. develop). These tests pin the resolution priority and the
``--base`` argument flowing into the gh invocation.
"""

from pathlib import Path
from typing import Any, List
from unittest.mock import patch, MagicMock

import pytest

from outbid_dirigent.shipper import Shipper


# ─── _resolve_base_branch ────────────────────────────────────────────────────


def _make_shipper(tmp_path: Path) -> Shipper:
    return Shipper(repo_path=tmp_path, plan=None, dry_run=False)


def test_env_var_wins_over_git_head(tmp_path: Path) -> None:
    """GIT_BRANCH (set by outbid-portal) reflects the FR's explicit choice and
    should beat whatever git happens to have checked out."""
    shipper = _make_shipper(tmp_path)
    with patch.dict("os.environ", {"GIT_BRANCH": "develop"}, clear=False):
        with patch("outbid_dirigent.shipper.subprocess.run") as run_mock:
            assert shipper._resolve_base_branch() == "develop"
            # git was never asked when env wins.
            run_mock.assert_not_called()


def test_falls_back_to_current_branch_when_env_missing(tmp_path: Path) -> None:
    shipper = _make_shipper(tmp_path)
    fake_result = MagicMock(returncode=0, stdout="develop\n", stderr="")
    with patch.dict("os.environ", {}, clear=True):
        with patch(
            "outbid_dirigent.shipper.subprocess.run",
            return_value=fake_result,
        ) as run_mock:
            assert shipper._resolve_base_branch() == "develop"
            args, _kwargs = run_mock.call_args
            assert args[0] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]


def test_returns_none_on_detached_head(tmp_path: Path) -> None:
    """Detached HEAD has no usable branch name — caller must omit ``--base``."""
    shipper = _make_shipper(tmp_path)
    fake_result = MagicMock(returncode=0, stdout="HEAD\n", stderr="")
    with patch.dict("os.environ", {}, clear=True):
        with patch(
            "outbid_dirigent.shipper.subprocess.run",
            return_value=fake_result,
        ):
            assert shipper._resolve_base_branch() is None


def test_returns_none_when_git_command_fails(tmp_path: Path) -> None:
    shipper = _make_shipper(tmp_path)
    fake_result = MagicMock(returncode=128, stdout="", stderr="not a git repo")
    with patch.dict("os.environ", {}, clear=True):
        with patch(
            "outbid_dirigent.shipper.subprocess.run",
            return_value=fake_result,
        ):
            assert shipper._resolve_base_branch() is None


def test_empty_env_var_falls_through(tmp_path: Path) -> None:
    """An empty GIT_BRANCH (deployment quirk) must not be treated as valid."""
    shipper = _make_shipper(tmp_path)
    fake_result = MagicMock(returncode=0, stdout="develop\n", stderr="")
    with patch.dict("os.environ", {"GIT_BRANCH": "  "}, clear=False):
        with patch(
            "outbid_dirigent.shipper.subprocess.run",
            return_value=fake_result,
        ) as run_mock:
            assert shipper._resolve_base_branch() == "develop"
            run_mock.assert_called_once()


# ─── gh pr create --base wiring ──────────────────────────────────────────────


def _ok(stdout: str = "") -> MagicMock:
    return MagicMock(returncode=0, stdout=stdout, stderr="")


@pytest.fixture
def shipper_for_ship(tmp_path: Path) -> Shipper:
    plan = MagicMock(title="Test Feature")
    s = Shipper(repo_path=tmp_path, plan=plan, dry_run=False)
    # _generate_pr_body and _strip_artifacts hit disk; stub them.
    s._generate_pr_body = MagicMock(return_value="body")  # type: ignore[method-assign]
    s._strip_artifacts = MagicMock()  # type: ignore[method-assign]
    return s


def _capture_gh_pr_call(run_mock: MagicMock) -> List[str]:
    """Find the ``gh pr create`` invocation among recorded subprocess calls."""
    for call in run_mock.call_args_list:
        argv = call.args[0] if call.args else call.kwargs.get("args", [])
        if len(argv) >= 3 and argv[0] == "gh" and argv[1] == "pr" and argv[2] == "create":
            return list(argv)
    raise AssertionError(
        f"gh pr create was not invoked. Calls: {run_mock.call_args_list}"
    )


def test_ship_passes_base_branch_from_env(shipper_for_ship: Shipper) -> None:
    """End-to-end: GIT_BRANCH=develop should land as ``--base develop`` in the
    gh invocation."""
    def side_effect(argv: List[str], **_: Any) -> MagicMock:
        # rev-parse --verify probes whether the dirigent/<slug> branch already
        # exists; returncode != 0 means "doesn't exist", which is what we want.
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return MagicMock(returncode=1, stdout="", stderr="")
        return _ok("https://github.com/x/y/pull/1")

    with patch.dict("os.environ", {"GIT_BRANCH": "develop"}, clear=False), \
         patch("outbid_dirigent.shipper.shutil.which", return_value="/usr/bin/gh"), \
         patch("outbid_dirigent.shipper.subprocess.run", side_effect=side_effect) as run_mock:
        assert shipper_for_ship.ship() is True

    argv = _capture_gh_pr_call(run_mock)
    assert "--base" in argv, f"--base flag missing from: {argv}"
    assert argv[argv.index("--base") + 1] == "develop"


def test_ship_omits_base_when_unresolved(shipper_for_ship: Shipper) -> None:
    """If neither env nor git can produce a base, gh must be invoked without
    ``--base`` so it can use the repo default rather than failing."""
    def side_effect(argv: List[str], **_: Any) -> MagicMock:
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return MagicMock(returncode=1, stdout="", stderr="")
        if argv[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return MagicMock(returncode=0, stdout="HEAD\n", stderr="")
        return _ok("https://github.com/x/y/pull/1")

    with patch.dict("os.environ", {}, clear=True), \
         patch("outbid_dirigent.shipper.shutil.which", return_value="/usr/bin/gh"), \
         patch("outbid_dirigent.shipper.subprocess.run", side_effect=side_effect) as run_mock:
        assert shipper_for_ship.ship() is True

    argv = _capture_gh_pr_call(run_mock)
    assert "--base" not in argv, f"--base should be absent, got: {argv}"
