import unittest
from pathlib import Path
from models.navigation_model import NavigationModel

class TestNavigationModel(unittest.TestCase):

    def test_initial_state_is_empty(self):
        model = NavigationModel()

        self.assertEqual(model.count(), 0)
        self.assertIsNone(model.current_image())
        self.assertFalse(model.can_next())
        self.assertFalse(model.can_previous())

    
    def test_set_images_initializes_correctly(self):
        images = [
            Path("a.jpg"),
            Path("b.jpg"),
            Path("c.jpg"),
        ]

        model = NavigationModel()
        model.set_images(images)

        self.assertEqual(model.count(), 3)
        self.assertEqual(model.current_index(), 0)
        self.assertEqual(model.current_image(), images[0])

    def test_next_and_previous(self):
        images = [Path("a.jpg"), Path("b.jpg")]
        model = NavigationModel()
        model.set_images(images)

        model.next()
        self.assertEqual(model.current_image(), images[1])

        model.previous()
        self.assertEqual(model.current_image(), images[0])


    def test_navigation_does_not_go_out_of_bounds(self):
        images = [Path("a.jpg"), Path("b.jpg")]
        model = NavigationModel()
        model.set_images(images)

        model.previous()
        self.assertEqual(model.current_index(), 0)

        model.next()
        model.next()
        self.assertEqual(model.current_index(), 1)

    def test_can_next_and_can_previous(self):
        images = [Path("a.jpg"), Path("b.jpg")]
        model = NavigationModel()
        model.set_images(images)

        self.assertFalse(model.can_previous())
        self.assertTrue(model.can_next())

        model.next()
        self.assertTrue(model.can_previous())
        self.assertFalse(model.can_next())

    def test_jump_to(self):
        images = [Path("a.jpg"), Path("b.jpg"), Path("c.jpg")]
        model = NavigationModel()
        model.set_images(images)

        model.jump_to(2)
        self.assertEqual(model.current_image(), images[2])

        model.jump_to(10)  # fuera de rango
        self.assertEqual(model.current_image(), images[2])

    def test_jump_relative(self):
        images = [Path("a.jpg"), Path("b.jpg"), Path("c.jpg")]
        model = NavigationModel()
        model.set_images(images)

        model.jump_relative(2)
        self.assertEqual(model.current_image(), images[2])

        model.jump_relative(-5)
        self.assertEqual(model.current_image(), images[0])
