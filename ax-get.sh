# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD
# VERSION 0.1.0

#! /bin/sh

major_ver=$1
minor_ver=$2
patch_ver=$3

function check_download () {
    if [ $1 -ne 0 ]; then
        echo "A fatal error has occured."
        echo "Unable to download file from $source"
        echo "Please ensure the major, minor, and patch version numbers are provided"
        echo
        echo "For example, running \"$0 6 0 8\" should download \"axelor-erp-v6.0.8.war\" from GitHub."
        exit 1
    fi
}

if [ $(echo $(whoami)) != "root" ]; then
    echo "A fatal error has occured."
    echo "$(whoami) is not root"
    echo "Please try again using sudo."
    exit 1
fi

if [ $1 == "--latest" ] || [ $2 == "--latest" ]; then
    latest_src=latest.tmp
    curl https://github.com/axelor/axelor-open-suite/releases/latest > $latest_src
    
    redirect_test=$(grep -o "redirected" < $latest_src)
    
    if [ -n $redirect_test ]; then
        latest_ver=$(grep -o [?0-99] < $latest_src)
        incr=0
        rm $latest_src
        
        for ver in $latest_ver; do
            incr=$((incr + 1))

            case $incr in
                1) major_ver=$ver;;
                2) minor_ver=$ver;;
                3) patch_ver=$ver;;
                default) break;
            esac
        done
    else
        echo "A fatal error has occured."
        echo "The redirect has failed."
        exit 1
    fi
fi

version="$major_ver"."$minor_ver"."$patch_ver"
filename=axelor-erp-v$version
filetype="war"

if [ $1 == "--src" ] || [ $2 == "--src" ]; then
    if [ $1 != "--latest" ] && [ $2 != "--latest" ]; then
        major_ver=$2
        minor_ver=$3
        patch_ver=$4
        version="$major_ver"."$minor_ver"."$patch_ver"
        filename=axelor-erp-v$version
    fi
    
    filetype="zip"
    source=https://github.com/axelor/open-suite-webapp/archive/refs/tags/v$version.$filetype
    wget $source -O axelor-webapp.tmp
    check_download $?
    
    source=https://github.com/axelor/axelor-open-suite/archive/refs/tags/v$version.$filetype
    wget $source -O axelor-open-suite.tmp
    check_download $?
    
    unzip axelor-webapp.tmp
    mv open-suite-webapp-$version $filename-src
    unzip axelor-open-suite.tmp
    mv axelor-open-suite-$version $filename-src/modules/axelor-open-suite
    mv $filename-src/modules/axelor-open-suite/axelor-open-suite-$version $filename-src/modules/axelor-open-suite-$version
    rm -rf $filename-src/modules/axelor-open-suite
    mv $filename-src/modules/axelor-open-suite-$version $filename-src/modules/axelor-open-suite
    rm axelor-webapp.tmp
    rm axelor-open-suite.tmp
else
    source=https://github.com/axelor/open-suite-webapp/releases/download/v$version/$filename.$filetype
    wget $source
    check_download $?
    
    unzip $filename.$filetype -d $filename
fi

chown -R tomcat:tomcat $filename
branding=0

if [ -f "branding_logo.png" ]; then
    cp branding_logo.png ./"$filename"/img/branding_logo.png
    chown tomcat:tomcat ./"$filename"/img/branding_logo.png
    branding=1
fi


