from pathlib import Path
import subprocess



class FileOpener:

    @staticmethod
    def reveal_file(path: Path) -> None:
        subprocess.run(
            ["explorer", "/select,", str(path)],
            check=False
        )