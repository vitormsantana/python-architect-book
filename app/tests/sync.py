import hashlib
import os
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def sync(source, dest):
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)

    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    for action, *paths in actions:
        if action == 'copy':
            shutil.copyfile(*paths)
        if action == 'move':
            shutil.move(*paths)
        if action == 'delete':
            os.remove(paths[0])

BLOCKSIZE = 65536
def hash_file(path):
    logger.debug(f"path: {path}")
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    logger.debug(f"hasher.hexdigest: {hasher.hexdigest}")
    return hasher.hexdigest

#hash_file('C:/Users/vitor/OneDrive/Documentos/python/gitRepoBookVitor/.gitignore')

def read_paths_and_hashes(root):
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    return hashes


def determine_actions(src_hashes, dst_hashes, src_folder, dst_folder):
    for sha, filename in src_hashes.items():
        if sha not in dst_hashes:
            sourcepath = Path(src_folder) / filename
            destpath = Path(dst_folder) / filename
            yield 'copy', sourcepath, destpath

        elif dst_hashes[sha] != filename:
            olddestpath = Path(dst_folder) / dst_hashes[sha]
            newdestpath = Path(dst_folder) / filename
            yield 'move', olddestpath, newdestpath

    for sha, filename in dst_hashes.items():
        if sha not in src_hashes:
            yield 'delete', dst_folder / filename


"""
def sync(source, dest):
    logger.debug(f"source: {source}")
    logger.debug(f"dest: {dest}")
    source_hashes = {}
    for folder, _, files in os.walk(source):
        for fn in files:
            logger.debug(f"source folder: {folder}")
            logger.debug(f"source _: {_}")
            logger.debug(f"source files: {files}")
            logger.debug(f"source fn: {fn}")

            source_hashes[hash_file(Path(folder) / fn)] = fn
            logger.debug(f"source_hashes: {source_hashes}")
            logger.debug(f"--------------------------------------")

    seen = set()
    for folder, _, files in os.walk(dest):
        for fn in files:
            logger.debug(f"dest folder: {folder}")
            logger.debug(f"dest _: {_}")
            logger.debug(f"dest files: {files}")
            logger.debug(f"dest fn: {fn}")

            dest_path = Path(folder) / fn
            dest_hash = hash_file(dest_path)
            logger.debug(f"dest_path: {dest_path}")
            logger.debug(f"dest_hash: {dest_hash}")

            seen.add(dest_hash)

            if dest_hash not in source_hashes:
                dest_path.unlink()

            elif dest_hash in source_hashes and fn != source_hashes[dest_hash]:
                shutil.move(dest_path, Path(folder) / source_hashes[dest_hash])
                logger.debug(f"moved ({dest_path}, {Path(folder)} / {source_hashes[dest_hash]})")


    for src_hash, fn in source_hashes.items():
        if src_hash not in seen:
            shutil.copy(Path(source) / fn, Path(dest) / fn)
            logger.debug(f"copied {Path(source)} / {fn}, {Path(dest)} / {fn}")

    # Print all repositories (source_hashes)
    logger.debug(f"All source repositories: {source_hashes}")

    # Print files in destination directory
    logger.debug(f"Files in destination directory {dest}:")
    for folder, _, files in os.walk(dest):
        for fn in files:
            logger.debug(f" - {Path(folder) / fn}")

# Sample usage (update with actual paths)
source = "C:/Users/vitor/OneDrive/Documentos/python/source"
dest = "C:/Users/vitor/OneDrive/Documentos/python/dest"

# Create some sample files in the source directory for testing
os.makedirs(source, exist_ok=True)
with open(f"{source}/file1.txt", "w") as f:
    f.write("This is a sample file 1.")
with open(f"{source}/file2.txt", "w") as f:
    f.write("This is a sample file 2.")

# Create some sample files in the destination directory for testing
os.makedirs(dest, exist_ok=True)
with open(f"{dest}/file2.txt", "w") as f:
    f.write("This is a different file 2.")
with open(f"{dest}/file3.txt", "w") as f:
    f.write("This is a sample file 3.")

# Run the sync function
sync(source, dest)
"""