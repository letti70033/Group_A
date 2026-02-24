from pathlib import Path
import requests
from types import SimpleNamespace

from app.okavango import OkavangoData


def test_download_dataset_creates_file(tmp_path, monkeypatch):
    """
    Test Function 1: download_dataset
    Ensures a file is written to downloads directory.
    """

    # Create instance without running __init__
    data = OkavangoData.__new__(OkavangoData)
    data.download_dir = tmp_path

    fake_content = b"Entity,Year,Code,Value\nPortugal,2020,PRT,123\n"

    # Mock requests.get
    def fake_get(*args, **kwargs):
        return SimpleNamespace(
            content=fake_content,
            raise_for_status=lambda: None
        )

    monkeypatch.setattr(requests, "get", fake_get)

    url = "https://ourworldindata.org/grapher/annual-deforestation.csv"
    data.download_dataset(url)

    output_file = tmp_path / "annual-deforestation.csv"

    assert output_file.exists()
    assert output_file.read_bytes() == fake_content