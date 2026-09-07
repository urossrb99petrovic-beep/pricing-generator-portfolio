import json
import sys
import tempfile
import unittest
from pathlib import Path
import getpass


APPLICATION_ROOT = (
    Path(__file__).resolve().parent.parent
)

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.services.logging_service import LoggingService


class TestLoggingService(unittest.TestCase):
    """
    Tests structured Pricing Generator logging.
    """

    def setUp(self) -> None:
        """
        Creates an isolated temporary project directory for
        every test.
        """

        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.project_root = Path(
            self.temporary_directory.name
        )

        self.logging_config = {
            "enabled": True,
            "directory": (
                "{project_root}/Administration/Logs"
            ),
            "folder_structure": (
                "{application_version}/{year}/{month}"
            ),
            "one_file_per_generation": True,
            "include_successful_generations": True,
            "include_failed_generations": True,
            "encoding": "utf-8",
            "format": "json"
        }

        self.logging_service = LoggingService(
            project_root=self.project_root,
            logging_config=self.logging_config,
            application_version="1.0.0"
        )

    def tearDown(self) -> None:
        """
        Removes the temporary test directory.
        """

        self.temporary_directory.cleanup()

    def test_creates_logging_service(
        self
    ) -> None:
        """
        Confirms LoggingService can be created with valid
        configuration.
        """

        self.assertIsInstance(
            self.logging_service,
            LoggingService
        )

    def test_success_log_is_created(
        self
    ) -> None:
        """
        Confirms a successful generation creates a JSON log.
        """

        output_file = (
            self.project_root
            / "output"
            / "USD - SMS - template Aug 2026.csv"
        )

        log_path = (
            self.logging_service.log_success(
                currency="USD",
                product="SMS",
                pricing_type="Baseline",
                sender_ids={
                    "US": "10DLC",
                    "CA": "TOLL_FREE"
                },
                local_countries=[],
                rows_generated=234,
                output_file=output_file
            )
        )

        self.assertIsNotNone(
            log_path
        )

        self.assertTrue(
            log_path.exists()
        )

        self.assertEqual(
            log_path.suffix,
            ".json"
        )

    def test_success_log_contains_expected_data(
        self
    ) -> None:
        """
        Confirms successful generation information is written
        correctly.
        """

        output_file = (
            self.project_root
            / "output"
            / "USD - Local SMS - template Aug 2026.csv"
        )

        log_path = (
            self.logging_service.log_success(
                currency="USD",
                product="Local SMS",
                pricing_type="Enterprise",
                sender_ids={
                    "US": "DSC",
                    "CA": "TOLL_FREE"
                },
                local_countries=[
                    "Serbia",
                    "Kenya"
                ],
                rows_generated=234,
                output_file=output_file
            )
        )

        with log_path.open(
            mode="r",
            encoding="utf-8"
        ) as log_file:
            log_data = json.load(
                log_file
            )

        self.assertEqual(
            log_data["status"],
            "SUCCESS"
        )

        self.assertEqual(
            log_data["application_version"],
            "1.0.0"
        )

        self.assertEqual(
            log_data["currency"],
            "USD"
        )

        self.assertEqual(
            log_data["product"],
            "Local SMS"
        )

        self.assertEqual(
            log_data["pricing_type"],
            "Enterprise"
        )

        self.assertEqual(
            log_data["sender_ids"],
            {
                "US": "DSC",
                "CA": "TOLL_FREE"
            }
        )

        self.assertEqual(
            log_data["local_countries"],
            [
                "Serbia",
                "Kenya"
            ]
        )

        self.assertEqual(
            log_data["rows_generated"],
            234
        )

        self.assertEqual(
            log_data["output_file"],
            output_file.name
        )

        self.assertIn(
            "timestamp",
            log_data
        )

    def test_failure_log_contains_error(
        self
    ) -> None:
        """
        Confirms failed generation logs contain useful error
        information.
        """

        error = ValueError(
            "Test generation failure."
        )

        log_path = (
            self.logging_service.log_failure(
                currency="EUR",
                product="Premium SMS",
                pricing_type="Baseline",
                sender_ids={
                    "US": "DSC",
                    "CA": "DSC"
                },
                local_countries=[],
                error=error
            )
        )

        self.assertIsNotNone(
            log_path
        )

        with log_path.open(
            mode="r",
            encoding="utf-8"
        ) as log_file:
            log_data = json.load(
                log_file
            )

        self.assertEqual(
            log_data["status"],
            "FAILED"
        )

        self.assertEqual(
            log_data["error_type"],
            "ValueError"
        )

        self.assertEqual(
            log_data["error_message"],
            "Test generation failure."
        )

    def test_creates_year_and_month_directories(
        self
    ) -> None:
        """
        Confirms missing log directories are created
        automatically.
        """

        output_file = (
            self.project_root
            / "test.csv"
        )

        log_path = (
            self.logging_service.log_success(
                currency="USD",
                product="SMS",
                pricing_type="Baseline",
                sender_ids={},
                local_countries=[],
                rows_generated=234,
                output_file=output_file
            )
        )

        self.assertTrue(
            log_path.parent.exists()
        )

        self.assertEqual(
            log_path.parent.parent.parent.name,
            "1.0.0"
        )

        self.assertEqual(
            len(log_path.parent.parent.name),
            4
        )

        self.assertEqual(
            len(log_path.parent.name),
            2
        )

    def test_existing_log_directories_are_reused(
        self
    ) -> None:
        """
        Confirms existing folders do not prevent another log
        from being written.
        """

        first_log = (
            self.logging_service.log_success(
                currency="USD",
                product="SMS",
                pricing_type="Baseline",
                sender_ids={},
                local_countries=[],
                rows_generated=234,
                output_file=(
                    self.project_root
                    / "first.csv"
                )
            )
        )

        second_log = (
            self.logging_service.log_failure(
                currency="EUR",
                product="SMS",
                pricing_type="Enterprise",
                sender_ids={},
                local_countries=[],
                error=ValueError(
                    "Second test."
                )
            )
        )

        self.assertTrue(
            first_log.parent.exists()
        )

        self.assertTrue(
            second_log.exists()
        )

    def test_disabled_logging_creates_no_file(
        self
    ) -> None:
        """
        Confirms globally disabled logging creates nothing.
        """

        config = self.logging_config.copy()

        config["enabled"] = False

        service = LoggingService(
            project_root=self.project_root,
            logging_config=config,
            application_version="1.0.0"
        )

        log_path = service.log_success(
            currency="USD",
            product="SMS",
            pricing_type="Baseline",
            sender_ids={},
            local_countries=[],
            rows_generated=234,
            output_file=(
                self.project_root
                / "test.csv"
            )
        )

        self.assertIsNone(
            log_path
        )

        logs_directory = (
            self.project_root
            / "Administration"
            / "Logs"
        )

        self.assertFalse(
            logs_directory.exists()
        )

    def test_success_logging_can_be_disabled(
        self
    ) -> None:
        """
        Confirms successful logs can be disabled separately.
        """

        config = self.logging_config.copy()

        config[
            "include_successful_generations"
        ] = False

        service = LoggingService(
            project_root=self.project_root,
            logging_config=config,
            application_version="1.0.0"
        )

        log_path = service.log_success(
            currency="USD",
            product="SMS",
            pricing_type="Baseline",
            sender_ids={},
            local_countries=[],
            rows_generated=234,
            output_file=(
                self.project_root
                / "test.csv"
            )
        )

        self.assertIsNone(
            log_path
        )

    def test_failure_logging_can_be_disabled(
        self
    ) -> None:
        """
        Confirms failed logs can be disabled separately.
        """

        config = self.logging_config.copy()

        config[
            "include_failed_generations"
        ] = False

        service = LoggingService(
            project_root=self.project_root,
            logging_config=config,
            application_version="1.0.0"
        )

        log_path = service.log_failure(
            currency="USD",
            product="SMS",
            pricing_type="Baseline",
            sender_ids={},
            local_countries=[],
            error=ValueError(
                "Expected test error."
            )
        )

        self.assertIsNone(
            log_path
        )

    def test_product_name_is_safe_for_filename(
        self
    ) -> None:
        """
        Confirms spaces and invalid Windows filename
        characters are removed from log filenames.
        """

        log_path = (
            self.logging_service.log_success(
                currency="USD",
                product="Local SMS/Test",
                pricing_type="Baseline",
                sender_ids={},
                local_countries=[],
                rows_generated=234,
                output_file=(
                    self.project_root
                    / "test.csv"
                )
            )
        )

        self.assertNotIn(
            "/",
            log_path.name
        )

        self.assertIn(
            "Local_SMS_Test",
            log_path.name
        )

    def test_unicode_values_are_preserved(
        self
    ) -> None:
        """
        Confirms JSON logging preserves Unicode text.
        """

        log_path = (
            self.logging_service.log_success(
                currency="EUR",
                product="Local SMS",
                pricing_type="Baseline",
                sender_ids={},
                local_countries=[
                    "Serbia",
                    "Côte d'Ivoire"
                ],
                rows_generated=234,
                output_file=(
                    self.project_root
                    / "test.csv"
                )
            )
        )

        log_text = log_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "Côte d'Ivoire",
            log_text
        )

    def test_log_contains_requesting_user(
        self
    ) -> None:
        """
        Confirms the Windows user who requested the generation
        is recorded in the log.
        """

        output_file = (
            self.project_root
            / "output"
            / "test.csv"
        )

        log_path = (
            self.logging_service.log_success(
                currency="USD",
                product="SMS",
                pricing_type="Baseline",
                sender_ids={
                    "US": "DSC",
                    "CA": "DSC"
                },
                local_countries=[],
                rows_generated=234,
                output_file=output_file
            )
        )

        with log_path.open(
            mode="r",
            encoding="utf-8"
        ) as log_file:
            log_data = json.load(
                log_file
            )

        self.assertIn(
            "requested_by",
            log_data
        )

        self.assertEqual(
            log_data["requested_by"],
            getpass.getuser()
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )