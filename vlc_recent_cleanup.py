#!/usr/bin/env python3
"""
Script for cleanup VLC player recently played files

Now supported:
  - remove files with specific extensions, e.g. "mp3" or "flac"
  - remove files under specific directories, e.g. "~/tmp"

Made for this thread:
  https://forum.videolan.org/viewtopic.php?f=7&t=167016
"""
import argparse
import dataclasses
import os
import plistlib
import sys
from typing import Set, Callable, Final, List

ShouldDropFileFunc = Callable[[str], bool]

MEDIA_LIST_KEY: Final = 'recentlyPlayedMediaList'
MEDIA_DICT_KEY: Final = 'recentlyPlayedMedia'
FILE_SCHEME: Final = 'file://'


def drop_files_by_user_func(*, plist: dict, should_drop_func: ShouldDropFileFunc, removed: Set[str]) -> None:
    # process recently played list
    if MEDIA_LIST_KEY in plist:
        filenames = plist[MEDIA_LIST_KEY]
        for name in list(filenames):
            if should_drop_func(name):
                # list could contain duplicates
                while name in filenames:
                    filenames.remove(name)
                    removed.add(name)

    # process dict with resume positions
    if MEDIA_DICT_KEY in plist:
        name2position = plist[MEDIA_DICT_KEY]
        keys = set(name2position.keys())
        for name in keys:
            if should_drop_func(name):
                name2position.pop(name, None)
                removed.add(name)


def drop_files_by_ext(*, plist: dict, extensions: Set[str], removed: Set[str]) -> None:
    extensions = {x.lower() for x in extensions}
    print('remove items with extensions:', repr(extensions))

    def should_drop(filename: str) -> bool:
        if not filename.startswith(FILE_SCHEME):
            return False
        ext = os.path.splitext(filename)[-1].lower()
        if ext.startswith('.'):
            ext = ext[1:]
        if not ext:
            return False
        return ext in extensions

    drop_files_by_user_func(plist=plist, should_drop_func=should_drop, removed=removed)


def cleanup_dir(dirname: str) -> str:
    dirname = os.path.abspath(os.path.expanduser(dirname))
    dirname = dirname.lower().rstrip(os.sep) + os.sep
    return dirname


def drop_files_inside_dirs(*, plist: dict, exclude_dirs: Set[str], removed: Set[str]) -> None:
    print('remove items inside subsirs:', repr(exclude_dirs))
    exclude_dirs = tuple(cleanup_dir(x) for x in exclude_dirs)

    def should_drop(filename: str) -> bool:
        if not filename.startswith(FILE_SCHEME):
            return False
        filename = filename[len(FILE_SCHEME):]
        filename = filename.lower()
        return filename.startswith(exclude_dirs)

    drop_files_by_user_func(plist=plist, should_drop_func=should_drop, removed=removed)


@dataclasses.dataclass(frozen=True)
class Config:
    drop_exts: Set[str]
    drop_dirs: Set[str]
    verbose: bool

    def __post_init__(self) -> None:
        if self.drop_exts:
            return
        if self.drop_dirs:
            return
        sys.exit('No cleanup options specified, nothing to do. Exit.')


def read_cli_config(args: List[str]) -> Config:
    parser = argparse.ArgumentParser(
        description='vlc_recent_cleanup - remove files from VLC Player\' recent list',
    )
    parser.add_argument(
        '--drop-ext',
        action='append',
        dest='drop_exts',
        help='remove files with specific extension (could be used many times)',
    )
    parser.add_argument(
        '--drop-dir',
        action='append',
        dest='drop_dirs',
        help='remove files under specific directory, e.g. "~/tmp" (could be used many times)',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='print removed items',
    )
    result = parser.parse_args(args)
    return Config(drop_exts=set(result.drop_exts), drop_dirs=set(result.drop_dirs), verbose=result.verbose)


def rename_file_to_backup(filename: str) -> None:
    bak_name = filename + '.bak'
    if os.path.isfile(bak_name):
        os.unlink(bak_name)
    if os.path.isfile(filename):
        os.rename(filename, bak_name)


def main(args: List[str]) -> None:
    config = read_cli_config(args)

    # https://images.videolan.org/support/faq.html#Config
    plist_filename = os.path.expanduser('~/Library/Preferences/org.videolan.vlc.plist')

    with open(plist_filename, 'rb') as inp:
        plist = plistlib.load(inp, fmt=plistlib.FMT_BINARY)

    removed: Set[str] = set()
    drop_files_by_ext(plist=plist, extensions=config.drop_exts, removed=removed)
    drop_files_inside_dirs(plist=plist, exclude_dirs=config.drop_dirs, removed=removed)

    rename_file_to_backup(plist_filename)

    with open(plist_filename, 'wb') as out:
        plistlib.dump(plist, out, fmt=plistlib.FMT_BINARY)

    if config.verbose:
        if removed:
            print('removed items:')
            for x in sorted(removed):
                print(x)
        else:
            print('no items removed.')


if __name__ == '__main__':
    if sys.platform != 'darwin':
        sys.exit('this script is for MacOS only')
    main(sys.argv[1:])
