#!/usr/bin/env bash

SCRIPTPATH=$( cd $(dirname $0) ; pwd -P )
ROOTPATH=$(dirname ${SCRIPTPATH})
BOOT2DOCKERPATH=${ROOTPATH}/images/boot2docker

pushd $BOOT2DOCKERPATH > /dev/null

get_vbox_version(){
    local VER
    VER=$(VBoxManage -v | awk -F "r" '{print $1}')
    if [ -z "$VER" ]; then
        echo "ERROR"
    else
        echo "$VER"
    fi

}

write_vbox_dockerfile(){
    local VER
    VER=$(get_vbox_version)
    if [ ! "$LATEST_RELEASE" = "ERROR" ]; then
        sed "s/\$VBOX_VERSION/$VER/g" Dockerfile.tmpl > Dockerfile
    else
        echo "WUH WOH"
    fi
}

echo 'Writing boot2docker Dockerfile'
write_vbox_dockerfile
echo 'Done!'

popd > /dev/null
