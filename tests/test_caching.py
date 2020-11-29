from typing import NamedTuple
from urllib.parse import urljoin

import pytest
import requests
import requests_mock

from iccas.caching import RemoteFolderProxy

BASE_URL = "http://www.whatever.com/path/to/folder/"


class RemoteFile(NamedTuple):
    folder_url: str
    relative_path: str
    content: bytes
    etag: str

    @property
    def url(self):
        return urljoin(self.folder_url, self.relative_path)

    def copy_with(self, content: bytes, etag: str):
        return RemoteFile(self.folder_url, self.relative_path, content, etag)


@pytest.fixture(scope="session")
def sample_file():
    return RemoteFile(
        folder_url=BASE_URL,
        relative_path="subpath/to/file.json",
        content="ciao!".encode("utf-8"),
        etag="ABC",
    )


@pytest.fixture
def remote_folder(tmp_path) -> RemoteFolderProxy:
    return RemoteFolderProxy(BASE_URL, tmp_path)


def get_content_callback(file: RemoteFile):
    # Emulate the server
    def content_callback(req: requests.Request, context):
        sent_etag = req.headers.get("If-None-Match", None)
        if sent_etag == file.etag:
            context.status_code = 304
            return b""
        else:
            context.headers["ETag"] = file.etag
            return file.content

    return content_callback


def setup_mocker(mocker, file: RemoteFile):
    return mocker.get(file.url, content=get_content_callback(file))


def test_file_is_downloaded_if_not_in_cache(remote_folder, sample_file):
    with requests_mock.Mocker() as mocker:
        setup_mocker(mocker, sample_file)
        local_path = remote_folder.get(sample_file.relative_path)
        assert local_path.read_bytes() == sample_file.content


def test_file_is_not_downloaded_if_etag_did_not_change(remote_folder, sample_file):
    with requests_mock.Mocker() as mocker:
        # Download a new file and annotate the creation time
        matcher = setup_mocker(mocker, sample_file)
        local_path = remote_folder.get(sample_file.relative_path)
        mtime_before = local_path.stat().st_mtime

        # Request the same file again
        remote_folder.get(sample_file.relative_path)
        # Check that the etag is sent with the request
        assert matcher.last_request.headers["If-None-Match"] == sample_file.etag
        # Check that the cached file remained untouched
        mtime_after = local_path.stat().st_mtime
        assert mtime_before == mtime_after


def test_cached_file_is_overwritten_if_etag_changed(remote_folder, sample_file):
    with requests_mock.Mocker() as mocker:
        # Download a new file
        setup_mocker(mocker, sample_file)
        remote_folder.get(sample_file.relative_path)
        # Simulate a modification in the remote file
        modified_file = sample_file.copy_with(content=b"new content", etag="newetag")
        matcher = setup_mocker(mocker, modified_file)
        # Request the same file again, expecting cache invalidation
        local_path = remote_folder.get(sample_file.relative_path)
        assert matcher.last_request.headers["If-None-Match"] == sample_file.etag
        assert local_path.read_bytes() == modified_file.content


def test_exception_is_raised_if_connection_error_and_file_not_cached(
    remote_folder, sample_file
):
    with requests_mock.Mocker() as mocker:
        # Request a file not in the cache and simulate a ConnectionError
        mocker.get(sample_file.url, exc=requests.exceptions.ConnectionError)
        with pytest.raises(ConnectionError):
            remote_folder.get(sample_file.relative_path)


def test_warning_is_raised_if_connection_error_and_file_in_cache(
    remote_folder, sample_file
):
    with requests_mock.Mocker() as mocker:
        # Request and download a new file
        setup_mocker(mocker, sample_file)
        remote_folder.get(sample_file.relative_path)

        # Request the same file but simulate a ConnectionError
        mocker.get(sample_file.url, exc=requests.exceptions.ConnectionError)
        with pytest.warns(
            UserWarning, match="Could not check if the remote file was modified"
        ):
            path = remote_folder.get(sample_file.relative_path)
        assert path is not None
