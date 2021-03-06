# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
import os
import requests
import shutil
import time
from warnings import warn

from ax_get.exceptions import (
    DirNotExistError,
    DirNotAccessibleError,
    NotFileError,
    InvalidBrandFile,
    FileAlreadyExists,
)
import ax_get.posix_compat as posix_compat
import ax_get.smartzip as smartzip
import ax_get.tmp_name as tmp_name

DEFAULT_BRANDING_FILE = "branding_logo.png"
PAUSE_SECONDS = 3
__version__ = "1.0.0"

# Source code wise, Axelor Open Suite depends on Axelor Open Webapp.
# Each url should provide binary WAR files with priority given to
# Open Suite.
default_opensuite_src_url = (
    "https://github.com/axelor/axelor-open-suite/archive/refs/tags/v"
)
default_opensuite_war_url = (
    "https://github.com/axelor/axelor-open-suite/releases/download/v"
)
default_openwebapp_src_url = (
    "https://github.com/axelor/open-suite-webapp/archive/refs/tags/v"
)
default_openwebapp_war_url = (
    "https://github.com/axelor/open-suite-webapp/releases/download/v"
)
default_war_basename = "axelor-erp-v"

# These variables need to be global in scope.
brand_path = ""
output_dir = ""
tomcat_id_tuple = posix_compat.get_tomcat_info()


def start():
    global brand_path
    global output_dir
    parser_dict = parse_args()
    # Deal with the version numbers.
    is_src = parser_dict["src"]
    major_ver = parser_dict["major"]
    minor_ver = parser_dict["minor"]
    patch_ver = parser_dict["patch"]
    ax_ver_str = major_ver + "." + minor_ver + "." + patch_ver
    # Deal with the filepaths.
    brand_path = parser_dict["brand_file"]
    output_dir = parser_dict["out"]
    # Check for valid filepaths and proper permissions.
    prep(is_src)

    action(ax_ver_str, is_src)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Grabs a copy of Axelor", epilog="Licensed under the 0BSD."
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument("-s", "--src", action="store_true")
    parser.add_argument(
        "-b", "--brand_file", default=DEFAULT_BRANDING_FILE, help="Path to logo"
    )
    parser.add_argument("-o", "--out", default=os.path.curdir, help="Output directory")
    parser.add_argument("major", help="Major version number")
    parser.add_argument("minor", help="Minor version number")
    parser.add_argument("patch", help="Patch version number")
    parser_dict = vars(parser.parse_args())
    return parser_dict


def prep(is_src):
    global brand_path
    global output_dir
    global tomcat_id_tuple

    # On POSIX-like platforms, the WAR file content should be
    # chowned for the tomcat user and group. Source code files
    # shouldn't be chowned.
    if tomcat_id_tuple and not is_src:
        if not posix_compat.make_root():
            warn("The downloaded Axelor content cannot be chowned")
            tomcat_id_tuple = ()

    # Start dealing with output_dir before brand_path,
    # for the latter might be relative, and thus, depend
    # on the current location of output_dir.
    # Check if directory exists.
    if not os.access(output_dir, os.F_OK):
        raise DirNotExistError(output_dir)
    # Check if the script needs to become root.
    if os.name == "posix" and not os.access(output_dir, os.R_OK ^ os.W_OK):
        if not posix_compat.make_root():
            raise DirNotAccessibleError(output_dir)
    os.chdir(output_dir)

    # Check if brand_path exists and is of a valid type
    # (not a directory or symlink). Only error out if it
    # is a user defined brand_path that doesn't exist.
    if not os.path.isfile(brand_path):
        # Only error out if it is a user defined
        # brand_path that doesn't exist or it
        # exists, but is not a file.
        if brand_path != DEFAULT_BRANDING_FILE:
            if os.path.exists(brand_path):
                raise NotFileError(brand_path)
            raise InvalidBrandFile(brand_path)
        # Set brand_path to empty string so boolean
        # operation will return False.
        brand_path = ""
    # Try to get permission to copy (read) brand_path.
    if brand_path and os.name == "posix" and not os.access(brand_path, os.R_OK):
        if not posix_compat.make_root():
            warn(f"Cannot read {brand_path}")
            brand_path = ""

    # Prepare for temporary file names.
    tmp_name.init(output_dir)


def action(ax_ver_str, is_src):
    # Used by both functions.
    brand_filename = os.path.basename(brand_path)

    if is_src:
        action_src(ax_ver_str, brand_filename)
    else:
        action_war(ax_ver_str, brand_filename)


def action_src(ax_ver_str, brand_filename):
    # The downloaded and extracted opensuite folder will
    # be placed inside a renamed openwebapp folder and that will
    # become the end result. The *zip_name variables are temporary
    # names assigned to the zip files downloaded, while the *folder_name
    # variables are what the extracted folder is temporarily called.
    # The final folder name for the end result is src_folder_name.
    opensuite_folder_name = tmp_name.get()
    openwebapp_folder_name = tmp_name.get()
    folder_name = "axelor-v" + ax_ver_str + "-src"

    # Path to application.properties. The config
    # file exists in both source and WAR files, but
    # in different locations.
    app_prop_path = os.path.join(
        output_dir,
        folder_name,
        "src",
        "main",
        "resources",
        "application.properties",
    )

    # Where the branding logo ends up also depends on whether the source code or
    # WAR file are being downloaded.
    brand_dest_path = os.path.join(
        output_dir, folder_name, "src", "main", "webapp", "img", brand_filename
    )

    folder_loc = os.path.join(output_dir, folder_name)
    if os.path.exists(folder_loc):
        raise FileAlreadyExists(folder_loc)
    action_src_openwebapp(ax_ver_str, openwebapp_folder_name)
    action_src_opensuite(ax_ver_str, opensuite_folder_name)

    os.rename(openwebapp_folder_name, folder_name)
    opensuite_dest = os.path.join(folder_name, "modules", "axelor-open-suite")
    os.rename(opensuite_folder_name, opensuite_dest)

    if brand_path:
        shutil.copyfile(brand_path, brand_dest_path)

    output_info(ax_ver_str, folder_name, app_prop_path, brand_dest_path, is_src=True)


def action_src_openwebapp(ax_ver_str, folder_name):
    src_url = default_openwebapp_src_url + ax_ver_str + ".zip"
    zip_name = tmp_name.get()

    webapp_src = requests.get(src_url)
    with open(zip_name, "wb") as webapp_fptr:
        for content in webapp_src.iter_content(chunk_size=40):
            webapp_fptr.write(content)
    # A separate with statement is used so that the file is completly downloaded
    # before extraction.
    with smartzip.SmartZip(zip_name, "r") as webapp_zip:
        webapp_zip.extractall(folder_name, remove_parent=True)
    os.remove(zip_name)


def action_src_opensuite(ax_ver_str, folder_name):
    src_url = default_opensuite_src_url + ax_ver_str + ".zip"
    zip_name = tmp_name.get()

    opensuite_src = requests.get(src_url)
    with open(zip_name, "wb") as opensuite_fptr:
        for content in opensuite_src.iter_content(chunk_size=40):
            opensuite_fptr.write(content)

    with smartzip.SmartZip(zip_name, "r") as opensuite_zip:
        opensuite_zip.extractall(folder_name, remove_parent=True)
    os.remove(zip_name)


def action_war(ax_ver_str, brand_filename):
    # Unlike when downloading the source code, both URLs aren't required
    # when downloading the WAR file. Rather, it attempts to download from the
    # opensuite_war_url first before falling back to the openwebapp_war_url.
    # war_name is the temporary name assigned to the downloaded WAR file,
    # while war_folder_name is what the final extracted product is renamed to.
    opensuite_url = (
        default_opensuite_war_url
        + ax_ver_str
        + "/"
        + default_war_basename
        + ax_ver_str
        + ".war"
    )
    openwebapp_url = (
        default_openwebapp_war_url
        + ax_ver_str
        + "/"
        + default_war_basename
        + ax_ver_str
        + ".war"
    )
    folder_name = "axelor-v" + ax_ver_str
    war_name = tmp_name.get()

    # Path to application.properties. The config
    # file exists in both source and WAR files, but
    # in different locations.
    app_prop_path = os.path.join(
        output_dir, folder_name, "WEB-INF", "classes", "application.properties"
    )

    # Where the branding logo ends up also depends on whether the source code or
    # WAR file are being downloaded.
    brand_dest_path = os.path.join(output_dir, folder_name, "img", brand_filename)

    folder_loc = os.path.join(output_dir, folder_name)
    if os.path.exists(folder_loc):
        raise FileAlreadyExists(folder_loc)

    try:
        war_file = requests.get(opensuite_url)
    except requests.exceptions.RequestException:
        war_file = requests.get(openwebapp_url)
    with open(war_name, "wb") as war_fptr:
        for content in war_file.iter_content(chunk_size=40):
            war_fptr.write(content)
    with smartzip.SmartZip(war_name, "r") as war_zip:
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        os.mkdir(folder_name)
        war_zip.extractall(folder_name, remove_parent=True)
    os.remove(war_name)
    if tomcat_id_tuple:
        posix_compat.chown_r(
            os.path.join(output_dir, folder_name),
            tomcat_id_tuple.uid,
            tomcat_id_tuple.gid,
        )

    if brand_path:
        shutil.copyfile(brand_path, brand_dest_path)

    output_info(ax_ver_str, folder_name, app_prop_path, brand_dest_path, is_src=False)


def output_info(ax_ver_str, folder_name, app_prop_path, brand_dest_path, is_src):
    if brand_path:
        brand_filename = os.path.basename(brand_dest_path)
        print(f"A personalized logo has been copied to {brand_dest_path}.")
        print(
            'Please edit the "application.logo" entry in'
            + app_prop_path
            + " to apply this new logo."
        )
        print('Typically, the entry will be set (by default) to "img/axelor.png".')
        print(f'Simply change this to "img/{brand_filename}".')
        print()
        time.sleep(PAUSE_SECONDS)
    print(
        "In order to get Axelor working, the "
        + app_prop_path
        + " file needs various database-related changes."
    )
    print()
    time.sleep(PAUSE_SECONDS)
    print(
        "More specifically, the name of the database its going to use and the db user account info that owns the database needs to be entered."
    )
    print(
        "This script does not generate a database for you, but please ensure that no databases used for this version were used by previous versions of Axelor."
    )
    print("This is to ensure a more reliable experience.")
    print(
        "To copy all the information from a previous instance of Axelor, please use the its built-in backup and restore feature."
    )
    print()
    time.sleep(PAUSE_SECONDS)
    print(
        "If a database hasn't been created already, it is recommended to name it after the specific version number you are running."
    )
    print("For example, axelor-" + ax_ver_str + " would make a great database name.")
    print(
        "This will make life easier in case it is necessary to revert to a previous version."
    )
    print(
        "In that case, there would be no need to worry about conflict due to a newer version of Axelor updating the database."
    )
    if not is_src:
        time.sleep(PAUSE_SECONDS)
        print()
        print(
            "In order to avoid having to specify "
            + folder_name
            + ' while typing in the URL or IP Address to access Axelor, please rename the folder to "ROOT".'
        )
