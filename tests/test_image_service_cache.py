import unittest
import unittest.mock
from pathlib import Path

from services.image_service import ImageService
from tests.fakes.fakes import FakeTagManager


class TestImageServiceFilterCache(unittest.TestCase):

    def setUp(self):
        self.tag_manager = FakeTagManager()
        self.service = ImageService(self.tag_manager)

        self.images = [
            Path("a.jpg"),
            Path("b.jpg"),
            Path("c.jpg"),
        ]

        # Mock Path.exists to return True
        self.patcher = unittest.mock.patch('pathlib.Path.exists', return_value=True)
        self.patcher.start()

        self.tag_manager.initialize_images(self.images)
        self.tag_manager.set_tags(self.images[0], ["cat"])
        self.tag_manager.set_tags(self.images[1], ["dog"])
        self.tag_manager.set_tags(self.images[2], [])

    def tearDown(self):
        self.patcher.stop()

    def test_filter_cache_hit(self):
        # Primera llamada → MISS
        result1 = self.service.filter_images(["cat"], [])

        self.assertEqual(self.tag_manager.filter_call_count, 1)
        self.assertEqual(result1, [Path("a.jpg")])

        # Segunda llamada → HIT
        result2 = self.service.filter_images(["cat"], [])

        self.assertEqual(self.tag_manager.filter_call_count, 1)  # 👈 no aumentó
        self.assertEqual(result2, result1)


    def test_filter_cache_invalidated_after_tag_change(self):
        # 1️⃣ Primera llamada → cache MISS
        result1 = self.service.filter_images(["cat"], [])
        self.assertEqual(result1, [Path("a.jpg")])
        self.assertEqual(self.tag_manager.filter_call_count, 1)

        # 2️⃣ Modificamos tags (esto debería invalidar el cache)
        self.service.add_tags(Path("c.jpg"), ["cat"])

        # 3️⃣ Segunda llamada con mismos filtros
        result2 = self.service.filter_images(["cat"], [])

        # 👉 Debe recalcular
        self.assertEqual(self.tag_manager.filter_call_count, 2)
        self.assertEqual(
            result2,
            [Path("a.jpg"), Path("c.jpg")]
        )