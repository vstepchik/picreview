import shutil
import tempfile
import time
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image

from app.repository import Repository
from app.workspace_mgr import WorkspaceManager


# It is integration test - uses real repo and fs
class WorkspaceManagerIntegrationTests(unittest.TestCase):
    test_dir: Path
    fs_timer_delta: timedelta
    repo: Repository

    mgr: WorkspaceManager

    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp(prefix="picreview_test_"))
        self.repo = Repository(db_file=Path(":memory:"))
        self.mgr = WorkspaceManager(repo=self.repo)
        self.fs_timer_delta = self.probe_fs_and_python_timers_discrepancy_delta()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def mk_img_file(self, img_relative_path: Path) -> Path:
        img = Image.new('RGB', (8, 8), color='white')
        path = self.test_dir.joinpath(img_relative_path)
        img.save(path)
        return path

    def probe_fs_and_python_timers_discrepancy_delta(self) -> timedelta:
        fs_timer_probe_file = self.test_dir.joinpath("_fs_timer_probe")
        fs_timer_probe_file.touch(exist_ok=True)
        python_time = datetime.now()
        fs_mod_time = datetime.fromtimestamp(fs_timer_probe_file.stat().st_mtime)
        return python_time - fs_mod_time

    def wait(self):
        time.sleep(0.05)

    def test_workspace_is_created_in_empty_dir(self):
        timestamp_before_create = datetime.now()
        self.wait()
        result = self.mgr.create_new_workspace(path=self.test_dir, name="empty test workspace", set_current=True)
        self.wait()
        timestamp_after_create = datetime.now()

        self.assertEqual(self.test_dir, self.mgr.get_current_workspace_dir())
        self.assertEqual("empty test workspace", self.mgr.current_workspace.name)
        self.assertEqual(self.repo.get_workspace(result.id), self.mgr.current_workspace)
        self.assertEqual([], self.repo.get_all_images_for_workspace(result.id))
        self.assertTrue(timestamp_before_create <= result.last_used_at <= timestamp_after_create)

    def test_workspace_is_created_in_dir_hierarchy_with_nested_images(self):
        timestamp_test_start = datetime.now()
        self.wait()
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
            self.mk_img_file(i)
        self.test_dir.joinpath(*"a/a.txt".split("/")).write_text("hi")  # should be ignored

        self.wait()
        timestamp_before_create = datetime.now()
        self.wait()
        result = self.mgr.create_new_workspace(path=self.test_dir, name="test WS with nested images", set_current=True)
        self.wait()
        timestamp_after_create = datetime.now()

        self.assertEqual(self.test_dir, self.mgr.get_current_workspace_dir())
        self.assertEqual("test WS with nested images", self.mgr.current_workspace.name)
        self.assertEqual(self.repo.get_workspace(result.id), self.mgr.current_workspace)
        self.assertTrue(timestamp_before_create <= result.last_used_at <= timestamp_after_create)

        images_in_db = self.repo.get_all_images_for_workspace(result.id)
        image_paths = set(self.test_dir.joinpath(i) for i in image_paths)
        self.assertSetEqual(image_paths, set(Path(i.path) for i in images_in_db))
        for i in images_in_db:
            msg = f"Failed on {i}, test start at {timestamp_test_start}, ws created after {timestamp_before_create}"
            self.assertTrue(i.workspace_id == result.id, msg=msg)
            self.assertTrue(i.size == Path(i.path).stat().st_size, msg=msg)
            self.assertTrue(i.width == 8 and i.height == 8, msg=msg)
            self.assertTrue(i.rank == 0, msg=msg)
            self.assertTrue(i.thumbnail, msg=msg)
            self.assertTrue(
                timestamp_test_start <= (i.last_updated_at + self.fs_timer_delta) <= timestamp_before_create,
                msg=msg,
            )

    def test_changes_in_workspace_are_detected_on_refresh(self):
        timestamp_test_start = datetime.now()
        self.wait()
        image_paths = [self.test_dir.joinpath(p) for p in ["a.png", "b.png", "c.png"]]
        for i in image_paths:
            self.mk_img_file(i)

        self.wait()
        timestamp_before_ws_created = datetime.now()
        self.wait()
        ws = self.mgr.create_new_workspace(path=self.test_dir, name="test WS refresh detects", set_current=True)

        db_images = self.repo.get_all_images_for_workspace(ws.id)
        self.assertSetEqual(set(image_paths), set(Path(i.path) for i in db_images))
        self.assertTrue(all(
            timestamp_test_start <= (i.last_updated_at + self.fs_timer_delta) <= timestamp_before_ws_created
            for i in db_images
        ))
        images_before_refresh = {Path(i.path).name: i for i in db_images}

        # d.png - new, c.png - deleted, a.png - updated
        self.mk_img_file(self.test_dir.joinpath("d.png"))
        self.test_dir.joinpath("c.png").unlink()
        self.mk_img_file(self.test_dir.joinpath("a.png"))

        self.mgr.refresh_current_workspace()

        db_images = self.repo.get_all_images_for_workspace(ws.id)
        image_paths = [self.test_dir.joinpath(p) for p in ["a.png", "b.png", "d.png"]]
        self.assertSetEqual(set(image_paths), set(Path(i.path) for i in db_images))
        images_after_refresh = {Path(i.path).name: i for i in db_images}
        self.assertEqual(images_before_refresh["b.png"].last_updated_at, images_after_refresh["b.png"].last_updated_at)
        self.assertTrue(images_before_refresh["a.png"].last_updated_at < images_after_refresh["a.png"].last_updated_at)

    def test_updated_image_rank_is_persisted_on_refresh(self):
        image_path = self.test_dir.joinpath("img.png")
        self.mk_img_file(image_path)

        ws = self.mgr.create_new_workspace(path=self.test_dir, name="test", set_current=True)

        db_images = self.repo.get_all_images_for_workspace(ws.id)
        self.assertEqual(1, len(db_images))
        db_image = db_images[0]
        self.assertEqual(0, db_image.rank)

        persisted_image = self.repo.persist_image(replace(db_image, rank=5))
        self.assertEqual(5, persisted_image.rank)

        self.wait()
        self.mk_img_file(image_path)  # update the file
        self.mgr.refresh_current_workspace()
        db_image_after_refresh = self.repo.get_image(ws.id, db_image.path)
        self.assertTrue(
            db_image_after_refresh.last_updated_at > db_image.last_updated_at,
            f"time difference is {db_image_after_refresh.last_updated_at - db_image.last_updated_at}",
        )
        self.assertEqual(5, db_image_after_refresh.rank)


if __name__ == "__main__":
    unittest.main()
