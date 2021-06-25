#!/usr/bin/env python3

# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
import os
import requests
import shutil
import sys

# So the instructions have a bit
# of a breather between them.
import time
import zipfile

# Add POSIX support (for becoming root and chowning).
import posix_compat

DIR_ERROR_CODE = 1
PERMISSION_ERROR_CODE = 2
INVALID_TYPE_ERROR_CODE = 3
INVALID_INPUT = 4

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
parser_args = parser.parse_args()

# Deal with the version numbers.
is_src = parser_args.src
major_ver = parser_args.major
minor_ver = parser_args.minor
patch_ver = parser_args.patch
ax_ver_str = major_ver + "." + minor_ver + "." + patch_ver

# On POSIX-like platforms, the WAR file content should be
# chowned for the tomcat user and group. Source code files
# shouldn't be chowned.
chownable = False
tomcat_tuple = posix_compat.get_tomcat_info()
if os.name == "posix" and not is_src:
    if tomcat_tuple.name is not None:
        if posix_compat.make_root():
            chownable = True
        else:
            print(
                "Warning: Downloaded Axelor content cannot be chowned.", file=sys.stderr
            )

# Start dealing with output_dir before brand_file,
# for the latter might be relative, and thus, depend
# on the current location of output_dir.
output_dir = os.path.abspath(parser_args.out)
# Check if directory exists.
if not os.access(output_dir, os.F_OK):
    print(f"FE: Directory {output_dir} does not exist.", file=sys.stderr)
    sys.exit(DIR_ERROR_CODE)
# Check if the script needs to become root.
if os.name == "posix" and not os.access(output_dir, os.R_OK ^ os.W_OK):
    if not posix_compat.make_root():
        print(f"FE: No permissions to access {output_dir}.", file=sys.stderr)
        sys.exit(PERMISSION_ERROR_CODE)
os.chdir(output_dir)

brand_file = parser_args.brand_file
if not os.path.isabs(brand_file):
    brand_file = os.path.abspath(brand_file)
# Check if brand_file exists and is of a valid type
# (not a directory or symlink).
use_brand_file = True
if not os.path.isfile(brand_file):
    use_brand_file = False
    if os.path.exists(brand_file):
        print(f"FE: The path {brand_file} is not a file.")
        sys.exit(INVALID_TYPE_ERROR_CODE)
    else:
        # Only error out if it is a user defined
        # brand_file that doesn't exist.
        if not brand_file == os.path.abspath(DEFAULT_BRANDING_FILE):
            print(f"FE: Given brand file of {brand_file} is invalid.")
            sys.exit(INVALID_INPUT)
# Try to get permission to copy (read) brand_file.
if use_brand_file and os.name == "posix" and not os.access(brand_file, os.R_OK):
    if not posix_compat.make_root():
        print(f"Warning: Cannot read {brand_file}.", file=sys.stderr)
brand_filename = os.path.basename(brand_file)

# The downloaded and extracted opensuite folder will
# be placed inside a renamed openwebapp folder and that will
# become the end result. The *zip_name variables are temporary
# names assigned to the zip files downloaded, while the *folder_name
# variables are what the extracted folder is temporarily called.
# The final folder name for the end result is src_folder_name.
opensuite_src_url = default_opensuite_src_url + ax_ver_str + ".zip"
opensuite_src_folder_name = "axelor-open-suite-" + ax_ver_str
opensuite_src_zip_name = "opensuite_src.zip"
openwebapp_src_url = default_openwebapp_src_url + ax_ver_str + ".zip"
openwebapp_src_folder_name = "open-suite-webapp-" + ax_ver_str
openwebapp_src_zip_name = "openwebapp_src.zip"
src_folder_name = "axelor-v" + ax_ver_str + "-src"

# Unlike when downloading the source code, both URLs aren't required
# when downloading the WAR file. Rather, it attempts to download from the
# opensuite_war_url first before falling back to the openwebapp_war_url.
# war_name is the temporary name assigned to the downloaded WAR file,
# while war_folder_name is what the final extracted product is renamed to.
opensuite_war_url = (
    default_opensuite_war_url
    + ax_ver_str
    + "/"
    + default_war_basename
    + ax_ver_str
    + ".war"
)
openwebapp_war_url = (
    default_openwebapp_war_url
    + ax_ver_str
    + "/"
    + default_war_basename
    + ax_ver_str
    + ".war"
)
war_folder_name = "axelor-v" + ax_ver_str
war_name = "axelor-v" + ax_ver_str + ".war"

# Path to application.properties. The config
# file exists in both source and WAR files, but
# in different locations.
app_prop_path = ""
app_prop_src = os.path.join(
    output_dir, src_folder_name, "src", "main", "resources", "application.properties"
)
app_prop_war = os.path.join(
    output_dir, war_folder_name, "WEB-INF", "classes", "application.properties"
)

# Where the branding logo ends up also depends on whether the source code or
# WAR file are being downloaded.
brand_dest_path = ""
brand_dest_src = os.path.join(
    output_dir, src_folder_name, "src", "main", "webapp", "img", brand_filename
)
brand_dest_war = os.path.join(output_dir, war_folder_name, "img", brand_filename)

if is_src:
    app_prop_path = app_prop_src
    brand_dest_path = brand_dest_src
    webapp_src = requests.get(openwebapp_src_url)
    with open(openwebapp_src_zip_name, "wb") as webapp_src_fp:
        for content in webapp_src.iter_content(chunk_size=40):
            webapp_src_fp.write(content)
    # A seperate with statement is used so that the file is completly downloaded
    # before extraction.
    with zipfile.ZipFile(openwebapp_src_zip_name, "r") as webapp_src_zip:
        webapp_src_zip.extractall()
    opensuite_src = requests.get(opensuite_src_url)
    with open(opensuite_src_zip_name, "wb") as opensuite_src_fp:
        for content in opensuite_src.iter_content(chunk_size=40):
            opensuite_src_fp.write(content)
    # Extract opensuite zip file into the correct location inside
    # openwebapp folder. After extraction, it will be in its own folder.
    # Because of this, it should be renamed to what its supposed to be and
    # any pre-existing folders with its expected name will be removed.
    with zipfile.ZipFile(opensuite_src_zip_name, "r") as opensuite_src_zip:
        opensuite_src_dest = os.path.join(
            openwebapp_src_folder_name, "modules", "axelor-open-suite"
        )
        opensuite_src_zip.extractall(os.path.dirname(opensuite_src_dest))
        if os.path.exists(opensuite_src_dest):
            shutil.rmtree(opensuite_src_dest)
        os.rename(
            os.path.join(
                os.path.dirname(opensuite_src_dest), opensuite_src_folder_name
            ),
            opensuite_src_dest,
        )
    os.remove(openwebapp_src_zip_name)
    os.remove(opensuite_src_zip_name)
    os.rename(openwebapp_src_folder_name, src_folder_name)
    if use_brand_file:
        shutil.copyfile(brand_file, brand_dest_path)
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
else:
    app_prop_path = app_prop_war
    brand_dest_path = brand_dest_war

    try:
        war_file = requests.get(opensuite_war_url)
    except requests.exceptions.RequestException:
        war_file = requests.get(openwebapp_war_url)
    with open(war_name, "wb") as war_fp:
        for content in war_file.iter_content(chunk_size=40):
            war_fp.write(content)
    with zipfile.ZipFile(war_name, "r") as war_zip:
        if os.path.exists(war_folder_name):
            shutil.rmtree(war_folder_name)
        os.mkdir(war_folder_name)
        for member in war_zip.infolist():
            war_zip.extract(member, war_folder_name)
    os.remove(war_name)
    if use_brand_file:
        shutil.copyfile(brand_file, brand_dest_path)
        print(f"A personalized logo has been copied to {brand_dest_path}.")
        print(
            'Please edit the "application.logo" entry in '
            + app_prop_path
            + " to apply this new logo."
        )
        print('Typically, the entry will be set (by default) to "img/axelor.png".')
        print(f'Simply change this to "img/{brand_filename}".')
        print()
        time.sleep(PAUSE_SECONDS)
    if chownable:
        posix_compat.chown_r(
            os.path.join(output_dir, war_folder_name),
            tomcat_tuple.uid,
            tomcat_tuple.gid,
        )

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
        + war_folder_name
        + ' while typing in the URL or IP Address to access Axelor, please rename the folder to "ROOT".'
    )
