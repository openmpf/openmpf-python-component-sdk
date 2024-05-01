# Overview

This directory contains the source code, test examples, and installation script
for the MPF NlpTextSplitter tool, which uses WtP and spaCy libraries
to detect sentences in a given chunk of text.

## Background

Our primary motivation for creating this tool was to find a lightweight, accurate
sentence detection capability to support a large variety of text processing tasks
including translation and tagging.

Through preliminary investigation, we identified the [WtP library ("Where's the
Point")](https://github.com/bminixhofer/wtpsplit) and [spaCy's multilingual sentence
detection model](https://spacy.io/models) for identifying sentence breaks
in a large section of text.

WtP models are trained to split up multilingual text by sentence without the need of an
input language tag. The disadvantage is that the most accurate WtP models will need ~3.5
GB of GPU memory. On the other hand, spaCy has a single multilingual sentence detection
that appears to work better for splitting up English text in certain cases, unfortunately
this model lacks support handling for Chinese punctuation.


## Installation of NlpTextSplitter: GPU vs CPU modes

To install this tool users will need to run:

`./install.sh`  - Which will setup a CPU-only PyTorch installation.

Please note that several customizations are supported:

- `--text-splitter-dir|-t <path_to_src>` This parameter specifies where the
  source code is located relative to the installation script. In general,
  since the installation script and source code are both located here, it's not
  necessary to update this parameter unless the user is running the `install.sh`
  script from a different directory.

- `--gpu ` - Add this parameter to the installation command line above to
  setup a PyTorch installation with CUDA (GPU) libraries.

- `--models-dir|-m <models-dir>`  - Add this parameter to
  change the default WtP model installation directory
  (default: `/opt/wtp/models`).

- `--install-wtp-model|-w <model-name>:` - Add this parameter to specify
  additional WTP models for installation. This parameter can be provided
  multiple times to install more than one model.

- `--install-spacy-model|-s <model-name>:` - Add this parameter to specify
  additional spaCy models for installation. This parameter can be provided
  multiple times to install more than one model.
