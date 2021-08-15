# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import collections
import copy
import getpass
import os
import sys

UserTuple = collections.namedtuple("UserTuple", ("name", "uid", "gid"))

if os.name == "posix":
    import pwd


def make_root():
    if os.name == "posix":
        if not getpass.getuser() == "root":
            # Need to perform a deep copy, as it
            # wouldn't be good to modify the original.
            script_arg_list = copy.deepcopy(sys.argv)
            # Try to get the absolute path to the
            # Python script so if one of the root-granting
            # programs error out, it might provide a more
            # useful error message.
            script_arg_list[0] = os.path.abspath(script_arg_list[0])
            # Make sure all arguments are converted to str.
            for index, arg in enumerate(script_arg_list):
                if not isinstance(arg, str):
                    script_arg_list[index] = str(arg)
            # Now the entire list can become a string that
            # can easily be used.
            script_args = " ".join(script_arg_list)
            if (
                os.system(f"pkexec {script_args}") == 0
                or os.system(f"sudo {script_args}") == 0
                or os.system(f"su root '{script_args}'") == 0
            ):
                # Need to exit out of script if the script
                # has already run as root once.
                sys.exit()
        # Must be root.
        return True
    # Default to False for non-POSIX platforms.
    return False


def get_tomcat_info():
    tomcat_name = "tomcat"
    tomcat_uid = -1
    tomcat_gid = -1
    if os.name == "posix":
        try:
            tomcat_info = pwd.getpwnam("tomcat")
            tomcat_uid = tomcat_info[2]
            tomcat_gid = tomcat_info[3]
        except KeyError:
            tomcat_name = None
    return UserTuple(tomcat_name, tomcat_uid, tomcat_gid)


# A recursive chown function.
def chown_r(path, uid, gid):
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        # Prospector complains that dirnames isn't used, otherwise.
        del dirnames
        os.chown(dirpath, uid, gid)
        for filename in filenames:
            os.chown(os.path.join(dirpath, filename), uid, gid)
