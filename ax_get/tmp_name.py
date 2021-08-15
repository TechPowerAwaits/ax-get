# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

"""Uses the tempfile module to create random file names."""

import collections
import os
import tempfile

# Since many values are going to be appended,
# use deque instead of a list.
tmp_name_tracker = collections.deque()


def init(target_dir=os.path.curdir):
    """Ensures that no name is going to conflict with one inside a given directory."""
    global tmp_name_tracker
    tmp_name_tracker.extend(os.listdir(target_dir))


def get():
    """Returns a tmp_name."""
    global tmp_name_tracker
    with tempfile.NamedTemporaryFile() as tmp_fptr:
        tmp_name = os.path.basename(tmp_fptr.name)
    # Get a new filename if name is already taken.
    if tmp_name in tmp_name_tracker:
        return get()
    # Mark filename as being used.
    tmp_name_tracker.append(tmp_name)
    return tmp_name
