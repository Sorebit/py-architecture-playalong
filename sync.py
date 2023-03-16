import hashlib
import os
import shutil
from pathlib import Path


class FileSystem:
    def read_paths_and_hashes(self, root):
        hashes = {}
        for folder, _, files in os.walk(root):
            for fn in files:
                hashes[hash_file(Path(folder) / fn)] = fn
        return hashes
    
    def copy(self, src, dst):
        shutil.copyfile(src, dst)
    
    def move(self, src, dst):
        shutil.move(src, dst)

    def remove(self, src):
        os.remove(src)


def sync(source, dest, filesystem=FileSystem()):
    # imperative shell step 1, gather inputs
    source_hashes = filesystem.read_paths_and_hashes(source)
    dest_hashes = filesystem.read_paths_and_hashes(dest)

    # step 2: call functional core
    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    # imperative shell step 3, apply outputs
    for action, *paths in actions:
        if action == "COPY":
            filesystem.copy(*paths)
        if action == "MOVE":
            filesystem.move(*paths)
        if action == "DELETE":
            filesystem.remove(paths[0])


BLOCKSIZE = 65536


def hash_file(path):
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


def determine_actions(source_hashes, dest_hashes, source_folder, dest_folder):
    for sha, filename in source_hashes.items():
        if sha not in dest_hashes:
            sourcepath = Path(source_folder) / filename
            destpath = Path(dest_folder) / filename
            yield "COPY", sourcepath, destpath

        elif dest_hashes[sha] != filename:
            olddestpath = Path(dest_folder) / dest_hashes[sha]
            newdestpath = Path(dest_folder) / filename
            yield "MOVE", olddestpath, newdestpath

    for sha, filename in dest_hashes.items():
        if sha not in source_hashes:
            yield "DELETE", dest_folder / filename
