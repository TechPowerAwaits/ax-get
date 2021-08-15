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
    """Ensures that no name is going to conflict with one inside the given directory."""
    global tmp_name_tracker
    tmp_name_tracker.extend(os.listdir(target_dir))
    if not tmp_name_tracker:
        # At least one string should be in
        # tmp_name_tracker, so it has to be
        # one that can never exist on the file
        # system.
        tmp_name_tracker.append("$TEMP$")


def get():
    """Returns a tmp_name."""
    global tmp_name_tracker
    # Needs something that is in tmp_name_tracker
    # so that the while loop will be entered at least
    # once.
    tmp_name = tmp_name_tracker[0]
    while tmp_name in tmp_name_tracker:
        with tempfile.NamedTemporaryFile() as tmp_fptr:
            tmp_name = tmp_fptr.name
    tmp_name_tracker.append(tmp_name)
    return tmp_name
