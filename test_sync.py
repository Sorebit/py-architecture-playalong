import tempfile
from pathlib import Path
import shutil
from sync import sync, determine_actions


class TestE2E:
    @staticmethod
    def test_when_a_file_exists_in_the_source_but_not_the_destination():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a very useful file"
            (Path(source) / "my-file").write_text(content)

            sync(source, dest)

            expected_path = Path(dest) / "my-file"
            assert expected_path.exists()
            assert expected_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)

    @staticmethod
    def test_when_a_file_has_been_renamed_in_the_source():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a file that was renamed"
            source_path = Path(source) / "source-filename"
            old_dest_path = Path(dest) / "dest-filename"
            expected_dest_path = Path(dest) / "source-filename"
            source_path.write_text(content)
            old_dest_path.write_text(content)

            sync(source, dest)

            assert old_dest_path.exists() is False
            assert expected_dest_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)


def test_when_a_file_exists_in_the_source_but_not_the_destination():
    source_hashes = {"hash1": "fn1"}
    dest_hashes = {}
    actions = determine_actions(source_hashes, dest_hashes, Path("/src"), Path("/dst"))
    assert list(actions) == [("COPY", Path("/src/fn1"), Path("/dst/fn1"))]


def test_when_a_file_has_been_renamed_in_the_source():
    source_hashes = {"hash1": "fn1"}
    dest_hashes = {"hash1": "fn2"}
    actions = determine_actions(source_hashes, dest_hashes, Path("/src"), Path("/dst"))
    assert list(actions) == [("MOVE", Path("/dst/fn2"), Path("/dst/fn1"))]


class FakeFileSystem:
    def __init__(self, path_hashes) -> None:
        self.path_hashes = path_hashes
        self.actions = []

    def read_paths_and_hashes(self, path):
        return self.path_hashes[path]
    
    def copy(self, src, dst):
        self.actions.append(("COPY", src, dst))
    
    def move(self, src, dst):
        self.actions.append(("MOVE", src, dst))

    def remove(self, src):
        self.actions.append(("REMOVE", src))


class TestEdgeToEdge:
    @staticmethod
    def test_when_a_file_exists_in_the_source_but_not_the_destination():
        fake_fs = FakeFileSystem({
            "/src": {"hash1": "fn1"},
            "/dst": {},
        })
        sync("/src", "/dst", fake_fs)
        assert fake_fs.actions == [("COPY", Path("/src/fn1"), Path("/dst/fn1"))]

    @staticmethod
    def test_when_a_file_has_been_renamed_in_the_source():
        fake_fs = FakeFileSystem({
            "/src": {"hash1": "fn1"},
            "/dst": {"hash1": "fn2"},
        })
        sync("/src", "/dst", fake_fs)
        assert fake_fs.actions == [("MOVE", Path("/dst/fn2"), Path("/dst/fn1"))]
