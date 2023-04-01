import dataclasses
import datetime
import unittest
from pathlib import Path
from sqlite3 import IntegrityError

from app.model.image_data import ImageData
from app.model.workspace import Workspace
from app.repository import Repository


class RepositoryTests(unittest.TestCase):
    repo: Repository

    def setUp(self) -> None:
        self.repo = Repository(Path(":memory:"))

    # WORKSPACE

    def test_workspace_persisted_with_null_id(self):
        ws = Workspace(
            id=None,
            name="test-workspace",
            path="foo/bar",
            last_used_at=datetime.datetime.now(),
        )

        persisted_ws = self.repo.persist_workspace(ws)

        self.assertEqual(1, persisted_ws.id)
        self.assertEqual(ws.name, persisted_ws.name)
        self.assertEqual(ws.path, persisted_ws.path)
        self.assertEqual(ws.last_used_at, persisted_ws.last_used_at)

        persisted_ws = self.repo.persist_workspace(ws)

        self.assertEqual(2, persisted_ws.id)
        self.assertEqual(ws.name, persisted_ws.name)
        self.assertEqual(ws.path, persisted_ws.path)
        self.assertEqual(ws.last_used_at, persisted_ws.last_used_at)

    def test_workspace_persisted_with_specified_id(self):
        ws = Workspace(
            id=9,
            name="test-workspace",
            path="foo/bar",
            last_used_at=datetime.datetime.now(),
        )

        persisted_ws = self.repo.persist_workspace(ws)

        self.assertEqual(ws.id, persisted_ws.id)
        self.assertEqual(ws.name, persisted_ws.name)
        self.assertEqual(ws.path, persisted_ws.path)
        self.assertEqual(ws.last_used_at, persisted_ws.last_used_at)

    def test_workspace_can_be_updated(self):
        ws = Workspace(
            id=3,
            name="name",
            path="foo/bar",
            last_used_at=datetime.datetime.now(),
        )
        persisted_ws = self.repo.persist_workspace(ws)
        changed_ws = dataclasses.replace(persisted_ws, name="updated name")

        updated_ws = self.repo.persist_workspace(changed_ws)

        self.assertEqual("name", persisted_ws.name)
        self.assertEqual("updated name", changed_ws.name)
        self.assertEqual("updated name", updated_ws.name)
        self.assertEqual(1, len(self.repo.get_all_workspaces()))

    def test_workspace_retrieved_by_id(self):
        ws = Workspace(
            id=1,
            name="test-workspace-get",
            path="2345",
            last_used_at=datetime.datetime.now(),
        )
        self.repo.persist_workspace(ws)

        retrieved = self.repo.get_workspace(1)
        self.assertEqual(ws, retrieved)

    def test_workspaces_can_be_listed(self):
        workspaces = []
        for i in range(20):
            ws = Workspace(
                id=None,
                name=f"test-workspace-{chr(i + ord('A'))}",
                path=f"test/list/{i}",
                last_used_at=datetime.datetime.now(),
            )
            workspaces.append(self.repo.persist_workspace(ws))

        result = self.repo.get_all_workspaces()
        self.assertEqual(len(workspaces), len(result))
        self.assertEqual(set(workspaces), set(result))

    def test_workspace_can_be_deleted(self):
        ws = Workspace(
            id=None,
            name="test-workspace-get",
            path="2345",
            last_used_at=datetime.datetime.now(),
        )
        created_ws_id = self.repo.persist_workspace(ws).id

        self.assertIsNotNone(self.repo.get_workspace(created_ws_id))

        self.repo.rm_workspace(created_ws_id)

        self.assertIsNone(self.repo.get_workspace(created_ws_id))

        self.repo.rm_workspace(created_ws_id)  # still works

    # IMAGE DATA #

    def test_image_can_be_persisted_for_workspace(self):
        ws = self.repo.persist_workspace(Workspace(
            id=None,
            name="test-workspace",
            path="foo/bar",
            last_used_at=datetime.datetime.now(),
        ))
        img = ImageData(
            workspace_id=ws.id,
            path="123",
            size=321,
            last_updated_at=datetime.datetime.now(),
            width=640,
            height=480,
            rank=3,
            thumbnail=b"Slava Ukraini!",
        )

        persisted_img = self.repo.persist_image(img)

        self.assertEqual(img, persisted_img)

    def test_image_can_be_updated(self):
        ws = self.repo.persist_workspace(Workspace(
            id=None,
            name="test-workspace",
            path="foo/bar",
            last_used_at=datetime.datetime.now(),
        ))
        img = self.repo.persist_image(ImageData(
            workspace_id=ws.id,
            path="123",
            size=321,
            last_updated_at=datetime.datetime.now(),
            width=640,
            height=480,
            rank=3,
            thumbnail=None,
        ))
        changed_img = dataclasses.replace(img, rank=7)
        updated_img = self.repo.persist_image(changed_img)

        self.assertEqual(7, updated_img.rank)
        self.assertEqual(7, self.repo.get_image(ws.id, img.path).rank)

    def test_image_can_not_be_persisted_without_workspace(self):
        img = ImageData(
            workspace_id=1,  # Workspace was never persisted
            path="123",
            size=321,
            last_updated_at=datetime.datetime.now(),
            width=640,
            height=480,
            rank=3,
            thumbnail=None,
        )
        self.assertRaises(IntegrityError, self.repo.persist_image, img)

    def test_image_with_the_same_path_can_exist_for_different_workspaces(self):
        ws1 = self.repo.persist_workspace(Workspace(
            id=None,
            name="WS 1",
            path="foo/bar/1",
            last_used_at=datetime.datetime.now(),
        ))
        ws2 = self.repo.persist_workspace(Workspace(
            id=None,
            name="WS 2",
            path="foo/bar/2",
            last_used_at=datetime.datetime.now(),
        ))
        img_path = "foo/bar/img.jpg"
        img1 = self.repo.persist_image(ImageData(
            workspace_id=ws1.id,
            path=img_path,
            size=321,
            last_updated_at=datetime.datetime.now(),
            width=640,
            height=480,
            rank=3,
            thumbnail=None,
        ))
        img2 = self.repo.persist_image(ImageData(
            workspace_id=ws2.id,
            path=img_path,
            size=222,
            last_updated_at=datetime.datetime.now(),
            width=640,
            height=480,
            rank=3,
            thumbnail=None,
        ))

        self.assertEqual(ws1.id, img1.workspace_id)
        self.assertEqual(img_path, img1.path)
        self.assertEqual(img1, self.repo.get_image(ws1.id, img_path))
        self.assertEqual(ws2.id, img2.workspace_id)
        self.assertEqual(img_path, img2.path)
        self.assertEqual(img2, self.repo.get_image(ws2.id, img_path))
        self.assertNotEqual(self.repo.get_image(ws1.id, img_path), self.repo.get_image(ws2.id, img_path))

    def test_images_can_be_listed_for_workspace(self):
        ws1 = self.repo.persist_workspace(Workspace(
            id=None,
            name="test-workspace-1",
            path="foo",
            last_used_at=datetime.datetime.now(),
        ))
        ws2 = self.repo.persist_workspace(Workspace(
            id=None,
            name="test-workspace-2",
            path="bar",
            last_used_at=datetime.datetime.now(),
        ))
        ws1_images = []
        for i in range(14):
            ws1_images.append(self.repo.persist_image(ImageData(
                workspace_id=ws1.id,
                path=f"{i}.png",
                size=100 + i * 20,
                last_updated_at=datetime.datetime.now(),
                width=640,
                height=480,
                rank=3 + i // 4,
                thumbnail=None,
            )))
        ws2_images = []
        for i in range(7):
            ws2_images.append(self.repo.persist_image(ImageData(
                workspace_id=ws2.id,
                path=f"{i+2}.png",
                size=100 + i * 20,
                last_updated_at=datetime.datetime.now(),
                width=640,
                height=480,
                rank=3 + i // 4,
                thumbnail=None,
            )))

        ws1_img_result = self.repo.get_all_images_for_workspace(ws1.id)
        ws2_img_result = self.repo.get_all_images_for_workspace(ws2.id)

        self.assertEqual(len(ws1_images), len(ws1_img_result))
        self.assertEqual(set(ws1_images), set(ws1_img_result))
        self.assertEqual(len(ws2_images), len(ws2_img_result))
        self.assertEqual(set(ws2_images), set(ws2_img_result))

    def test_image_can_deleted(self):
        ws = self.repo.persist_workspace(Workspace(
            id=None,
            name="test-workspace-to-delete",
            path="foo/bar",
            last_used_at=datetime.datetime.now(),
        ))
        img = self.repo.persist_image(ImageData(
            workspace_id=ws.id,
            path="123",
            size=321,
            last_updated_at=datetime.datetime.now(),
            width=640,
            height=480,
            rank=3,
            thumbnail=None,
        ))

        self.assertIsNotNone(self.repo.get_image(img.workspace_id, img.path))

        self.repo.rm_image(img.workspace_id, img.path)

        self.assertIsNone(self.repo.get_image(img.workspace_id, img.path))

        self.repo.rm_image(img.workspace_id, img.path)  # still works

    def test_images_are_cascade_deleted_with_workspace(self):
        ws1 = self.repo.persist_workspace(Workspace(
            id=None,
            name="test-workspace-1",
            path="foo",
            last_used_at=datetime.datetime.now(),
        ))
        ws2 = self.repo.persist_workspace(Workspace(
            id=None,
            name="test-workspace-2-to-delete",
            path="bar",
            last_used_at=datetime.datetime.now(),
        ))
        for i in range(14):
            self.repo.persist_image(ImageData(
                workspace_id=ws1.id,
                path=f"{i}.png",
                size=100 + i * 20,
                last_updated_at=datetime.datetime.now(),
                width=640,
                height=480,
                rank=3 + i // 4,
                thumbnail=None,
            ))
        for i in range(7):
            self.repo.persist_image(ImageData(
                workspace_id=ws2.id,
                path=f"{i+2}.png",
                size=100 + i * 20,
                last_updated_at=datetime.datetime.now(),
                width=640,
                height=480,
                rank=3 + i // 4,
                thumbnail=None,
            ))

        self.assertEqual(14, len(self.repo.get_all_images_for_workspace(ws1.id)))
        self.assertEqual(7, len(self.repo.get_all_images_for_workspace(ws2.id)))

        self.repo.rm_workspace(ws1.id)

        self.assertEqual(0, len(self.repo.get_all_images_for_workspace(ws1.id)))
        self.assertEqual(7, len(self.repo.get_all_images_for_workspace(ws2.id)))

    def test_image_outdated_check(self):
        now = datetime.datetime.now()
        ws = self.repo.persist_workspace(Workspace(
            id=None,
            name="test-workspace-to-update-image",
            path="foo/bar",
            last_used_at=now,
        ))
        img = self.repo.persist_image(ImageData(
            workspace_id=ws.id,
            path="123",
            size=321,
            last_updated_at=now,
            width=640,
            height=480,
            rank=3,
            thumbnail=None,
        ))

        one_microsecond = datetime.timedelta(microseconds=1)
        self.assertFalse(self.repo.is_image_outdated(img.workspace_id, img.path, now - one_microsecond))
        self.assertFalse(self.repo.is_image_outdated(img.workspace_id, img.path, now))
        self.assertTrue(self.repo.is_image_outdated(img.workspace_id, img.path, now + one_microsecond))

        # non-existing image is considered outdated
        self.assertTrue(self.repo.is_image_outdated(img.workspace_id, f"{img.path}-not-exists", now - one_microsecond))
        self.assertTrue(self.repo.is_image_outdated(img.workspace_id, f"{img.path}-not-exists", now))
        self.assertTrue(self.repo.is_image_outdated(img.workspace_id, f"{img.path}-not-exists", now + one_microsecond))


if __name__ == "__main__":
    unittest.main()
