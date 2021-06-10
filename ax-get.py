# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

import argparse
import os
import requests
import shutil

# So the instructions have a bit
# of a breather between them.
import time
import zipfile

PAUSE_SECONDS = 3

current_path = os.path.dirname(__file__)
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
    description="Grabs a copy of Axelor",
    epilog="Licensed under the 0BSD.")
parser.add_argument("-v", "--version", action="version", version=__version__)
parser.add_argument("-s", "--src", action="store_true")
parser.add_argument("major", help="Major version number")
parser.add_argument("minor", help="Minor version number")
parser.add_argument("patch", help="Patch version number")
parser_args = parser.parse_args()
is_src = parser_args.src
major_ver = parser_args.major
minor_ver = parser_args.minor
patch_ver = parser_args.patch
ax_ver_str = major_ver + "." + minor_ver + "." + patch_ver

opensuite_src_url = default_opensuite_src_url + ax_ver_str + ".zip"
opensuite_war_url = (
    default_opensuite_war_url
    + ax_ver_str
    + "/"
    + default_war_basename
    + ax_ver_str
    + ".war"
)
opensuite_src_zip_name = "opensuite_src.zip"
opensuite_src_folder_name = "axelor-open-suite-" + ax_ver_str
openwebapp_src_url = default_openwebapp_src_url + ax_ver_str + ".zip"
openwebapp_war_url = (
    default_openwebapp_war_url
    + ax_ver_str
    + "/"
    + default_war_basename
    + ax_ver_str
    + ".war"
)
openwebapp_src_folder_name = "open-suite-webapp-" + ax_ver_str
openwebapp_src_zip_name = "openwebapp_src.zip"
src_name = "axelor-v" + ax_ver_str + "-src"
war_name = "axelor-v" + ax_ver_str + ".war"
war_folder_name = "axelor-v" + ax_ver_str

# Path to application.properties
app_prop_path = ""

if is_src:
    webapp_src = requests.get(openwebapp_src_url)
    with open(openwebapp_src_zip_name, "wb") as webapp_src_fp:
        for content in webapp_src.iter_content(chunk_size=40):
            webapp_src_fp.write(content)
    with zipfile.ZipFile(openwebapp_src_zip_name, "r") as webapp_src_zip:
        webapp_src_zip.extractall()
    opensuite_src = requests.get(opensuite_src_url)
    with open(opensuite_src_zip_name, "wb") as opensuite_src_fp:
        for content in opensuite_src.iter_content(chunk_size=40):
            opensuite_src_fp.write(content)
    with zipfile.ZipFile(opensuite_src_zip_name, "r") as opensuite_src_zip:
        opensuite_src_dest = os.path.join(
            current_path, openwebapp_src_folder_name, "modules", "axelor-open-suite"
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
    os.rename(openwebapp_src_folder_name, src_name)
    app_prop_path = os.path.join(
        src_name, "src", "main", "resources", "application.properties"
    )
    if os.path.exists("branding_logo.png"):
        brand_path = os.path.join(
            src_name, "src", "main", "webapp", "img", "branding_logo.png"
        )
        shutil.copyfile("branding_logo.png", brand_path)
        print("A personalized logo has been copied to " + brand_path + ".")
        print(
            'Please edit the "application.logo" entry in '
            + app_prop_path
            + " to apply this new logo."
        )
        print('Typically, the entry will be set (by default) to "img/axelor.png".')
        print('Simply change this to "img/branding_logo.png".')
        print()
        time.sleep(PAUSE_SECONDS)
else:
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
    app_prop_path = os.path.join(
        war_folder_name, "WEB-INF", "classes", "application.properties"
    )
    if os.path.exists("branding_logo.png"):
        brand_path = os.path.join(war_folder_name, "img", "branding_logo.png")
        shutil.copyfile("branding_logo.png", brand_path)
        print("A personalized logo has been copied to " + brand_path + ".")
        print(
            'Please edit the "application.logo" entry in '
            + app_prop_path
            + " to apply this new logo."
        )
        print('Typically, the entry will be set (by default) to "img/axelor.png".')
        print('Simply change this to "img/branding_logo.png".')
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
        + war_folder_name
        + ' while typing in the URL or IP Address to access Axelor, please rename the folder to "ROOT".'
    )
