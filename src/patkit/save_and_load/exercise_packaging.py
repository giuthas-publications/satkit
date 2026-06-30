"""
Utility functions for packaging and importing Patkit Exercises.
"""

from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path

from patkit.constants import SourceSuffix


def package_exercise_to_zip(
    session_path: Path,
    zip_path: Path,
    active_answer_name: str,
    include_textgrids: bool = False,
) -> None:
    """
    Package a Patkit Session and Exercise into a zip file.

    Parameters
    ----------
    session_path : Path
        The root directory of the Session.
    zip_filepath : Path
        The destination path for the output `.zip` file.
    active_answer_name : str
        The name of the specific answer to include in the archive. It will be
        renamed to 'answer' in the resulting zip structure.
    include_textgrids : bool, optional
        Whether to include root-level `.TextGrid` files, by default False.
    """
    with ZipFile(file=zip_path, mode='w', compression=ZIP_DEFLATED) as output:
        for item in session_path.rglob('*'):
            if not item.is_file():
                continue

            rel_path = item.relative_to(session_path)

            # Filter root-level TextGrids
            if (
                not include_textgrids and
                len(rel_path.parts) == 1 and
                (rel_path.suffix.lower() == SourceSuffix.TEXTGRID.lower())
            ):
                continue

            # Process the exercise directory to filter answers
            if rel_path.parts[0] == 'exercise':
                if len(rel_path.parts) >= 3 and rel_path.parts[1] == 'answers':
                    # Only include the targeted answer,
                    # and rename it to 'answer'
                    if rel_path.parts[2] == active_answer_name:
                        new_parts = list(rel_path.parts)
                        new_parts[2] = 'answer'
                        arcname = Path(*new_parts)
                        output.write(filename=item, arcname=arcname)
                    continue  # Skip all other answer directories

            # Write all other allowed files
            output.write(filename=item, arcname=rel_path)


def unpackage_exercise_from_zip(
    zip_filepath: Path,
    destination_directory: Path
) -> None:
    """
    Extract a Patkit Exercise zip archive.

    Parameters
    ----------
    zip_filepath : Path
        The path to the `.zip` file to extract.
    destination_directory : Path
        The folder where the archive's contents should be unpacked.
    """
    with ZipFile(file=zip_filepath, mode='r') as zip_file:
        zip_file.extractall(path=destination_directory)
