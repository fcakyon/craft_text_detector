import os
import unittest
import craft_text_detector


class TestCraftTextDetector(unittest.TestCase):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(root_dir, '../figures/idcard.png')

    def test_load_craftnet_model(self):
        craft_net = craft_text_detector.load_craftnet_model()
        self.assertTrue(craft_net)

    def test_load_refinenet_model(self):
        refine_net = craft_text_detector.load_refinenet_model()
        self.assertTrue(refine_net)

    def test_get_prediction(self):
        # load image
        image = craft_text_detector.read_image(self.image_path)

        # load models
        craft_net = craft_text_detector.load_craftnet_model()
        refine_net = None

        # perform prediction
        text_threshold = 0.9
        link_threshold = 0.2
        low_text = 0.2
        cuda = False
        show_time = False
        get_prediction = craft_text_detector.get_prediction
        bboxes, polys, heatmap = get_prediction(image=image,
                                                craft_net=craft_net,
                                                refine_net=refine_net,
                                                text_threshold=text_threshold,
                                                link_threshold=link_threshold,
                                                low_text=low_text,
                                                cuda=cuda,
                                                show_time=show_time)
        self.assertEqual(len(bboxes), 49)
        self.assertEqual(len(bboxes[0]), 4)
        self.assertEqual(len(bboxes[0][0]), 2)
        self.assertEqual(int(bboxes[0][0][0]), 112)
        self.assertEqual(len(polys), 49)
        self.assertEqual(heatmap.shape, (384, 1184, 3))

    def test_detect_text(self):
        bboxes, _, _ = craft_text_detector.detect_text(self.image_path)
        self.assertEqual(len(bboxes), 56)
        self.assertEqual(len(bboxes[0]), 4)
        self.assertEqual(len(bboxes[0][0]), 2)
        self.assertEqual(int(bboxes[0][0][0]), 114)

        bboxes, _, _ = craft_text_detector.detect_text(self.image_path,
                                                       refiner=True)
        self.assertEqual(len(bboxes), 19)
        self.assertEqual(len(bboxes[0]), 4)
        self.assertEqual(len(bboxes[0][0]), 2)
        self.assertEqual(int(bboxes[0][0][0]), 114)


if __name__ == '__main__':
    unittest.main()