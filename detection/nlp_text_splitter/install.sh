#!/usr/bin/env bash

#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2024 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2024 The MITRE Corporation                                      #
#                                                                           #
# Licensed under the Apache License, Version 2.0 (the "License");           #
# you may not use this file except in compliance with the License.          #
# You may obtain a copy of the License at                                   #
#                                                                           #
#    http://www.apache.org/licenses/LICENSE-2.0                             #
#                                                                           #
# Unless required by applicable law or agreed to in writing, software       #
# distributed under the License is distributed on an "AS IS" BASIS,         #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
# See the License for the specific language governing permissions and       #
# limitations under the License.                                            #
#############################################################################

set -o errexit -o pipefail

main() {
    if ! options=$(getopt --name "$0"  \
            --options t:gm:w:s: \
            --longoptions text-splitter-dir:,gpu,wtp-models-dir:,install-wtp-model:,install-spacy-model: \
            -- "$@"); then
        print_usage
    fi
    eval set -- "$options"
    local wtp_models_dir=/opt/wtp/models
    local wtp_models=("wtp-bert-mini")
    local spacy_models=("xx_sent_ud_sm")
    while true; do
        case "$1" in
        --text-splitter-dir | -t )
            shift
            local text_splitter_dir=$1
            ;;
        --gpu | -g )
            local gpu_enabled=true
            ;;
        --wtp-models-dir  | -m )
            shift
            wtp_models_dir=$1;
            ;;
        --install-wtp-model | -w )
            shift
            wtp_models+=("$1")
            ;;
        --install-spacy-model | -s )
            shift
            spacy_models+=("$1")
            ;;
        -- )
            shift
            break
            ;;
        esac
        shift
    done

    install_text_splitter "$text_splitter_dir"
    install_py_torch "$gpu_enabled"
    download_wtp_models "$wtp_models_dir" "${wtp_models[@]}"
    download_spacy_models "${spacy_models[@]}"
}


install_text_splitter() {
    local text_splitter_dir=$1
    if [[ ! $text_splitter_dir ]]; then
        text_splitter_dir=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
    fi

    echo "Installing text splitter from source directory: $text_splitter_dir"
    pip3 install "$text_splitter_dir"
}


install_py_torch() {
    local gpu_enabled=$1
    local torch_package='torch~=2.3'
    if [[ $gpu_enabled ]]; then
        echo "Installing GPU enabled PyTorch."
        pip3 install "$torch_package"
    else
        echo "Installing CPU only version of PyTorch."
        pip3 install "$torch_package" --index-url https://download.pytorch.org/whl/cpu
    fi
}


download_wtp_models() {
    local wtp_models_dir=$1
    shift
    local model_names=("$@")
    setup_wtp_models_dir "$wtp_models_dir"

    for model_name in "${model_names[@]}"; do
        echo "Downloading the $model_name model to $wtp_models_dir."
        local wtp_model_dir="$wtp_models_dir/$model_name"
        python3 -c \
            "from huggingface_hub import snapshot_download; \
            snapshot_download('benjamin/$model_name', local_dir='$wtp_model_dir')"
    done
}

setup_wtp_models_dir() {
    local wtp_models_dir=$1

    if [[ ! $REQUESTS_CA_BUNDLE ]]; then
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    fi

    if ! mkdir --parents "$wtp_models_dir"; then
        echo "ERROR: Failed to create the $wtp_models_dir directory."
        exit 3
    fi

    if [[ ! -w "$wtp_models_dir" ]]; then
        echo -n "ERROR: The model directory, \"$wtp_models_dir\" is not writable by the current user. "
        echo "The permissions on \"$wtp_models_dir\" must be modified."
        exit 4
    fi
}

download_spacy_models() {
    for model_name in "$@"; do
        echo "Downloading the $model_name spaCy model."
        python3 -m spacy download "$model_name"
    done
}


print_usage() {
    echo
    echo "Usage:
$0 [--text-splitter-dir|-t <path_to_src>] [--gpu|-g] [--wtp-models-dir |-m <wtp-models-dir >] [--install-wtp-model|-w <model-name>]* [--install-spacy-model|-s <model-name>]*
Options
    --text-splitter-dir, -t <path>:    Path to text splitter source code. (defaults to to the
                                       same directory as this script)
    --gpu, -g:                         Install the GPU version of PyTorch
    --wtp-models-dir , -m <path>:      Path where WTP models will be stored.
                                       (defaults to /opt/wtp/models)
    --install-wtp-model, -w <name>:    Name of a WTP model to install in addtion to wtp-bert-mini.
                                       This option can be provided more than once to specify
                                       multiple models.
    --install-spacy-model | -s <name>: Names of a spaCy model to install in addtion to
                                       xx_sent_ud_sm. The option can be provided more than once
                                       to specify multiple models.
"
    exit 1
}

main "$@"
