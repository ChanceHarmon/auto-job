from datetime import date

from auto_job import storage
from auto_job.models import Job


def test_save_and_get_recent_jobs_preserves_match_details(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "auto_job.db")

    storage.init_db()

    job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="test",
        posting_url="https://example.com/jobs/1",
        location="Remote",
        remote_status="remote",
        salary="$100k",
        date_posted=date(2026, 5, 15),
        description="Python APIs PostgreSQL",
        detected_stack=["python", "postgresql"],
        match_reasons=["keyword match: backend engineer", "remote"],
        match_score=55,
    )

    was_saved = storage.save_job(job)
    recent_jobs = storage.get_recent_jobs()

    assert was_saved is True
    assert len(recent_jobs) == 1
    assert recent_jobs[0].detected_stack == ["python", "postgresql"]
    assert recent_jobs[0].match_reasons == [
        "keyword match: backend engineer",
        "remote",
    ]
    assert recent_jobs[0].match_score == 55
