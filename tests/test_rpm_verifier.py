"""Test rpm_verifier.py end-to-end"""

from pathlib import Path
from unittest.mock import MagicMock, call, create_autospec, sentinel

import pytest
from pytest import MonkeyPatch

from verify_rpms import rpm_verifier
from verify_rpms.rpm_verifier import ImageProcessor, ProcessedImage, generate_output


class TestImageProcessor:
    """Test ImageProcessor's callable"""

    @pytest.fixture()
    def mock_db_getter(self) -> MagicMock:
        "mocked db_getter function"
        return MagicMock()

    @pytest.fixture()
    def mock_rpms_getter(self) -> MagicMock:
        "mocked rpms_getter function"
        return MagicMock()

    @pytest.mark.parametrize(
        ("unsigned_rpms"),
        [
            pytest.param([], id="all signed"),
            pytest.param(["my-unsigned-rpm"], id="one unsigned"),
            pytest.param(
                ["my-unsigned-rpm", "their-unsigned-rpm"], id="multiple unsigned"
            ),
        ],
    )
    def test_call(
        self,
        mock_db_getter: MagicMock,
        mock_rpms_getter: MagicMock,
        tmp_path: Path,
        unsigned_rpms: list[str],
    ) -> None:
        """Test ImageProcessor's callable"""
        mock_rpms_getter.return_value = unsigned_rpms
        instance = ImageProcessor(
            workdir=tmp_path,
            db_getter=mock_db_getter,
            rpms_getter=mock_rpms_getter,
        )
        img = "my-img"
        out = instance(img)
        assert out == ProcessedImage(image=img, unsigned_rpms=unsigned_rpms)


class TestMain:
    """Test call to rpm_verifier.py main function"""

    @pytest.fixture()
    def mock_image_processor(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched ImageProcessor"""
        mock: MagicMock = create_autospec(
            ImageProcessor,
            return_value=MagicMock(return_value=sentinel.output),
        )
        monkeypatch.setattr(rpm_verifier, ImageProcessor.__name__, mock)
        return mock

    @pytest.fixture()
    def mock_generate_output(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched generate_output"""
        mock = create_autospec(generate_output)
        monkeypatch.setattr(rpm_verifier, generate_output.__name__, mock)
        return mock

    def test_main(
        self,
        mock_generate_output: MagicMock,
        mock_image_processor: MagicMock,
    ) -> None:
        """Test call to rpm_verifier.py main function"""
        rpm_verifier.main(  # pylint: disable=no-value-for-parameter
            args=[
                "--input",
                "img1",
                "--fail-unsigned",
                "true",
                "--workdir",
                "some/path",
            ],
            obj={},
            standalone_mode=False,
        )

        assert mock_image_processor.return_value.call_count == 1
        mock_image_processor.return_value.assert_has_calls([call("img1")])
        mock_generate_output.assert_called_once_with([sentinel.output], True)
