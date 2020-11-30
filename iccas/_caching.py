import json
import os
from _warnings import warn
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urljoin

import requests

from iccas.types import PathType

METADATA_FNAME = ".meta.json"


class RemoteFolderProxy:
    def __init__(self, folder_url: str, local_path: PathType):
        """
        Mirrors a "remote folder" lazily downloading and caching its files.

        The caching mechanism uses only ETags (If-Modified-Since is not supported
        by raw.github).
        You should not modify files inside the cache folder; if you do, the file
        will be re-downloaded and overwritten at the next call of get().
        """
        self.folder_url = folder_url
        self.local_path = Path(local_path)
        self.local_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.local_path / METADATA_FNAME
        if not self.metadata_path.exists():
            _write_json(self.metadata_path, {})

    def get(self, relative_path, force_download: bool = False) -> Path:
        """
        Ensures the latest version of a remote file is available locally in the
        cache, downloading it only if needed.
        If no internet connection is available (or the server is unreachable),
        the file available in the cache is returned with a warning; if the file
        is not in the cache, a ``ConnectionError`` is raised.

        Args:
            relative_path:
            force_download:

        Returns:
            full local path of the file
        """
        path = self.get_path_of(relative_path)
        full_json = _read_json(self.metadata_path)
        entries = full_json[self.folder_url] if self.folder_url in full_json else {}
        if relative_path not in entries:
            entries[relative_path] = {}

        if (
            not force_download
            and path.exists()
            and entries[relative_path].get("creationTime") == os.path.getmtime(path)
        ):
            current_etag = entries[relative_path].get("ETag", "")
        else:
            current_etag = ""

        try:
            url = urljoin(self.folder_url, relative_path)
            resp = _download_if_modified(url, path, current_etag)
            if resp:
                entries[relative_path] = {
                    "ETag": resp.headers.get("ETag"),
                    "creationTime": os.path.getmtime(path),
                }
                full_json[self.folder_url] = entries
                _write_json(self.metadata_path, full_json)
        except requests.exceptions.ConnectionError as exc:
            if force_download:
                raise ConnectionError(
                    f"set force_download=False to use the local cached version"
                    f"of the file (if available).\nError details: {exc}"
                )
            if path.exists():
                warn(
                    f"Could not check if the remote file was modified: {exc}\n"
                    f"However, a file is available in the local cache."
                )
            else:
                raise ConnectionError(
                    "unable to download the dataset and no dataset was "
                    "previously downloaded.\nDetails: {}".format(exc)
                )
        return path

    def get_path_of(self, relative_url) -> Path:
        return Path(self.local_path, unquote(relative_url))


def _download_if_modified(
    url: str, path: PathType, etag: str
) -> Optional[requests.Response]:
    """ If the remote resource was modified, returns its new ETag, otherwise None. """
    path = Path(path)
    resp = requests.get(url, headers={"If-None-Match": etag})
    if resp.status_code == 304:
        return None
    else:
        resp.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(resp.content)
        return resp


def _read_json(path: PathType) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: PathType, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
