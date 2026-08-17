from pathlib import Path

from patkit.configuration import PathStructure, SessionConfig
from patkit.constants import DatasourceNames
from patkit.data_structures import (
    Exercise, Session,
    ExerciseMetadata, FileInformation
)
from patkit.save_and_load import load_exercise, save_exercise


def test_answer_cursor_save_and_load(tmp_path: Path) -> None:
    """
    Verify that an Answer's cursor position is accurately preserved
    when an Exercise is saved to disk and subsequently loaded.
    """
    # Setup minimal dependencies for the Exercise
    file_info = FileInformation(patkit_path=tmp_path)
    path_structure = PathStructure(root=tmp_path)
    session = Session(
        name="test_session",
        config=SessionConfig(
            data_source_name=DatasourceNames.WAV,
            path_structure=path_structure),
        file_info=file_info
    )

    ex_metadata = ExerciseMetadata()
    exercise = Exercise(
        scenario=session,
        name="TestExercise",
        metadata=ex_metadata,
        file_info=file_info
    )

    # Create a new answer and artificially advance the cursor
    exercise.new_blank_answer(cursor=0, name="TestAnswer")
    answer = exercise["TestAnswer"]

    # Move the cursor to simulate user interaction
    expected_cursor_position = 2
    answer.cursor = expected_cursor_position

    # Save the exercise to the temporary path
    save_exercise(exercise=exercise)

    # Load the exercise from the temporary path
    loaded_exercise = load_exercise(directory=tmp_path, scenario=session)
    loaded_answer = loaded_exercise["TestAnswer"]

    # Assert the cursor state natively crashes if invalid
    assert loaded_answer.cursor == expected_cursor_position
