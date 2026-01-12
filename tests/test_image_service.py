import unittest
from pathlib import Path

from services.image_service import ImageService
from tests.fakes.fakes import FakeTagManager


class TestImageService(unittest.TestCase):

    def setUp(self):
        self.tag_manager = FakeTagManager()
        self.service = ImageService(self.tag_manager)

        self.img1 = Path("a.jpg")
        self.img2 = Path("b.jpg")
        self.img3 = Path("c.jpg")

        self.tag_manager.initialize_images([self.img1, self.img2, self.img3])

        self.tag_manager.set_tags(self.img1, ["cat", "cute"])
        self.tag_manager.set_tags(self.img2, ["dog"])
        self.tag_manager.set_tags(self.img3, ["cat", "wild"])


    def test_no_filters_returns_all_images(self):
        result = self.service.filter_images([], [])
        self.assertCountEqual(result, [self.img1, self.img2, self.img3])


    def test_positive_tag_filter(self):
        result = self.service.filter_images(["cat"], [])
        self.assertCountEqual(result, [self.img1, self.img3])


    def test_negative_tag_filter(self):
        result = self.service.filter_images([], ["dog"])
        self.assertCountEqual(result, [self.img1, self.img3])


    def test_positive_and_negative_filter(self):
        result = self.service.filter_images(["cat"], ["wild"])
        self.assertEqual(result, [self.img1])


    def test_filter_returns_empty_list_when_no_match(self):
        result = self.service.filter_images(["unicorn"], [])
        self.assertEqual(result, [])
