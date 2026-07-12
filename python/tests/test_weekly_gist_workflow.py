from pathlib import Path


def test_weekly_gist_checks_out_dispatch_branch_and_main_for_scheduled_runs():
    workflow = (
        Path(__file__).resolve().parents[2] / ".github" / "workflows" / "weekly-gist.yml"
    ).read_text(encoding="utf-8")

    assert (
        "      - uses: actions/checkout@v4\n"
        "        with:\n"
        "          ref: ${{ github.event_name == 'workflow_dispatch' && github.ref || 'main' }}\n"
    ) in workflow


def test_weekly_gist_commits_atomic_review_package_for_obsidian_sync():
    workflow = (
        Path(__file__).resolve().parents[2] / ".github" / "workflows" / "weekly-gist.yml"
    ).read_text(encoding="utf-8")

    assert "python -m rexy review build" in workflow
    assert "Weekly_Gist/Review_Packages/${END_DATE}/${{ github.run_id }}" in workflow
    assert "uses: actions/upload-artifact@v4" not in workflow
