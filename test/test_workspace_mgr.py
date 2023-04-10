import shutil
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY, call

from PIL import Image

from app.model.image_data import ImageData
from app.model.workspace import Workspace
from app.repository import Repository
from app.workspace_mgr import WorkspaceManager


class WorkspaceManagerTests(unittest.TestCase):
    test_dir: Path
    repo_mock: MagicMock

    mgr: WorkspaceManager

    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp(prefix="picreview_test_"))
        self.repo_mock = MagicMock(spec=Repository)
        self.mgr = WorkspaceManager(repo=self.repo_mock)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def mk_tmp_img(self, img_relative_path: Path):
        img = Image.new('RGB', (8, 8), color='white')
        img.save(self.test_dir.joinpath(img_relative_path))

    def test_workspace_is_created_in_empty_dir(self):
        fixed_now = datetime.now()
        expected_workspace = Workspace(
            id=None,
            name="empty test workspace",
            path=str(self.test_dir),
            last_used_at=fixed_now,
        )
        expected_persisted_workspace = replace(expected_workspace, id=1)
        self.repo_mock.persist_workspace.return_value = expected_persisted_workspace

        with patch('app.workspace_mgr.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            self.mgr.create_new_workspace(path=self.test_dir, name="empty test workspace", set_current=True)

        self.repo_mock.persist_workspace.assert_called_once_with(expected_workspace)
        self.assertEqual(self.test_dir, self.mgr.get_current_workspace_dir())
        self.assertEqual(expected_persisted_workspace, self.mgr.current_workspace)
        self.repo_mock.persist_image.assert_not_called()

    def test_workspace_is_created_in_dir_hierarchy_with_nested_images(self):
        fixed_now = datetime.now()
        image_paths = [
            "ws_root.png",
            "a/1.png",
            "a/2.png",
            "a/a.png",
            "a/a.bmp",
            "a/a.jpg",
            "a/a.jpeg",
            "a/a.gif",
            "a/a.tiff",
            "a/a/foo.png",
            "a/a/a/foo.png",
            "a/c/a/a/a/bar.png",
        ]
        for d in [p.split("/") for p in ["a/a/a", "a/b", "a/c/a/a/a/a/a", "a/c/b"]]:
            self.test_dir.joinpath(*d).mkdir(parents=True, exist_ok=True)
        for i in [Path(*p.split("/")) for p in image_paths]:
            self.mk_tmp_img(i)
        self.test_dir.joinpath(*"a/a.txt".split("/")).write_text("hi")

        expected_workspace = Workspace(
            id=None,
            name="test WS with nested images",
            path=str(self.test_dir),
            last_used_at=fixed_now,
        )
        expected_persisted_workspace = replace(expected_workspace, id=5)
        self.repo_mock.persist_workspace.return_value = expected_persisted_workspace

        with patch('app.workspace_mgr.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            self.mgr.create_new_workspace(path=self.test_dir, name="test WS with nested images", set_current=True)

        self.repo_mock.persist_workspace.assert_called_once_with(expected_workspace)
        self.assertEqual(self.test_dir, self.mgr.get_current_workspace_dir())
        self.assertEqual(expected_persisted_workspace, self.mgr.current_workspace)

        expected_image = ImageData(
            workspace_id=expected_persisted_workspace.id,
            path=ANY,
            size=ANY,
            last_updated_at=ANY,
            width=8,
            height=8,
            rank=0,
            thumbnail=ANY,
        )
        calls = [call(replace(expected_image, path=str(self.test_dir.joinpath(*p.split("/"))))) for p in image_paths]
        self.repo_mock.persist_image.assert_has_calls(calls, any_order=True)


if __name__ == "__main__":
    unittest.main()
