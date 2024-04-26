#!/usr/bin/env bash

set -o errexit -o pipefail


main() {
    if ! options=$(getopt --name "$0"  \
            --options t:gm: \
            --longoptions text-splitter-dir:,gpu,models-dir: \
            -- "$@"); then
        print_usage
    fi
    eval set -- "$options"
    while true; do
        case "$1" in
        --text-splitter-dir | -t )
            shift
            local text_splitter_dir=$1
            ;;
        --gpu | -g )
            local gpu_enabled=true
            ;;
        --models-dir | -m )
            shift
            local models_dir=$1;
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
    download_models "$models_dir"
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
        # networkx is a dependency of PyTorch, but the version of networkx in the PyTorch package
        # index requires Python 3.9. networkx needs to be installed in a separate command so that
        # pip can get networkx from PyPi.
        pip3 install 'networkx~=3.1'
        pip3 install "$torch_package" --index-url https://download.pytorch.org/whl/cpu
    fi
}

download_models() {
    local models_dir=${1:-/opt/wtp/models}

    if [[ ! $REQUESTS_CA_BUNDLE ]]; then
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    fi

    echo 'Downloading the xx_sent_ud_sm Spacy model.'
    python3 -m spacy download xx_sent_ud_sm

    echo "Downloading the wtp-bert-mini model to $models_dir."

    if ! mkdir --parents "$models_dir"; then
        echo "ERROR: Failed to create the $models_dir directory."
        exit 3
    fi

    if [[ ! -w "$models_dir" ]]; then
        echo -n "ERROR: The model directory, \"$models_dir\" is not writable by the current user. "
        echo "The permissions on \"$models_dir\" must be modified."
        exit 4
    fi

    local bert_model_dir="$models_dir"/wtp-bert-mini
    python3 -c \
        "from huggingface_hub import snapshot_download; \
        snapshot_download('benjamin/wtp-bert-mini', local_dir='$bert_model_dir')"
}


print_usage() {
    echo
    echo "Usage:
$0 [--text-splitter-dir|-t <path_to_src>] [--gpu|-g] [--models-dir|-m <models-dir>]"
    exit 1
}

main "$@"
