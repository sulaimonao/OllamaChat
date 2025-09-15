from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import types
import asyncio
from fastapi import UploadFile

sys.modules.setdefault("paddleocr", MagicMock())
sys.modules.setdefault("paddlepaddle", MagicMock())
sys.modules.setdefault("paddlex", MagicMock())
fw = MagicMock()
fw.WhisperModel.return_value.transcribe.return_value = ([], None)
sys.modules.setdefault("faster_whisper", fw)
sd = types.ModuleType("scenedetect")
sd.open_video = MagicMock()
sd.SceneManager = MagicMock()
det_mod = types.ModuleType("scenedetect.detectors")
det_mod.ContentDetector = MagicMock()
sm_mod = types.ModuleType("scenedetect.scene_manager")
sm_mod.save_images = MagicMock(return_value={})
sys.modules.setdefault("scenedetect", sd)
sys.modules.setdefault("scenedetect.detectors", det_mod)
sys.modules.setdefault("scenedetect.scene_manager", sm_mod)

from backend.tools.multimodal import video_analyze, MM_DIR


@patch("backend.tools.multimodal.subprocess.run")
@patch("backend.tools.multimodal.open_video")
@patch("backend.tools.multimodal.SceneManager")
def test_video_fallback(mock_sm, mock_open, mock_run):
    mock_open.return_value = MagicMock()
    sm_inst = MagicMock()
    sm_inst.get_scene_list.return_value = []
    mock_sm.return_value = sm_inst
    mock_run.return_value = MagicMock()

    tmp = MM_DIR / "tmp" / "test.mp4"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(b"fake")
    upload = UploadFile(filename="test.mp4", file=BytesIO(b"fake"))

    with patch("backend.tools.multimodal._save_temp", return_value=tmp):
        res = asyncio.run(video_analyze(upload))
    assert res.summary.startswith("No keyframes detected")
    assert res.scenes == []
