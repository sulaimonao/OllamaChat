import unittest
from pydantic import ValidationError
import os, sys, types

# Stub heavy dependencies before importing multimodal module
sys.modules['torch'] = types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda: False))

class _DummyModel:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()
    def __call__(self, *args, **kwargs):
        return {}
    def generate(self, *args, **kwargs):
        return [[0]]
    def decode(self, *args, **kwargs):
        return ""

sys.modules['transformers'] = types.SimpleNamespace(
    BlipProcessor=_DummyModel,
    BlipForConditionalGeneration=_DummyModel,
)
sys.modules['paddleocr'] = types.SimpleNamespace(PaddleOCR=lambda *a, **k: None)
class _DummyWhisper:
    def __init__(self, *a, **k):
        pass
    def transcribe(self, *a, **k):
        return [], None
sys.modules['faster_whisper'] = types.SimpleNamespace(WhisperModel=_DummyWhisper)

scenedetect_module = types.SimpleNamespace(
    open_video=lambda *a, **k: None,
    SceneManager=lambda *a, **k: types.SimpleNamespace(
        add_detector=lambda *a, **k: None,
        detect_scenes=lambda *a, **k: None,
        get_scene_list=lambda: []
    ),
)
sys.modules['scenedetect'] = scenedetect_module
sys.modules['scenedetect.detectors'] = types.SimpleNamespace(ContentDetector=lambda *a, **k: None)
sys.modules['scenedetect.scene_manager'] = types.SimpleNamespace(save_images=lambda *a, **k: {})
sys.modules['tools.search_engine'] = types.SimpleNamespace(SearchEngine=lambda *a, **k: None)

# Add the backend directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.multimodal import Scene, VideoAnalysisResponse

class TestSceneModel(unittest.TestCase):
    def test_scene_requires_t_and_path(self):
        with self.assertRaises(ValidationError):
            Scene(path='frame.jpg')
        with self.assertRaises(ValidationError):
            Scene(t=1.0)
        scene = Scene(t=1.0, path='frame.jpg')
        self.assertEqual(scene.t, 1.0)
        self.assertEqual(scene.path, 'frame.jpg')
        self.assertIsNone(scene.caption)
        self.assertIsNone(scene.ocr)

    def test_video_analysis_response_validates_scenes(self):
        invalid_scene = {'t': 1.0}
        with self.assertRaises(ValidationError):
            VideoAnalysisResponse(summary='s', scenes=[invalid_scene], transcript='t', artifact_path='p')
        scenes = [Scene(t=0.0, path='f.jpg')]
        resp = VideoAnalysisResponse(summary='s', scenes=scenes, transcript='t', artifact_path='p')
        self.assertEqual(resp.scenes[0].path, 'f.jpg')

if __name__ == '__main__':
    unittest.main()
