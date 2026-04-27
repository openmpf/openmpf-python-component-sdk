# Overview

This directory contains the source code, test examples, and installation script
for the OpenMPF NlpTextSplitter tool, which uses **SaT (Segment any Text)**,
**WtP (Where's the Point)**, and **spaCy** to detect sentences in a given chunk of text.

# Background

Our primary motivation for creating this tool was to find a lightweight, accurate
sentence detection capability to support a large variety of text processing tasks
including translation and tagging.

Through preliminary investigation, we identified the [WtP/SaT library ("Where's the
Point"/"Segment any Text")](https://github.com/bminixhofer/wtpsplit) and [spaCy's multilingual sentence
detection model](https://spacy.io/models) for identifying sentence breaks
in a large section of text.

WtP models are trained to split up multilingual text by sentence without the need of an
input language tag. The disadvantage is that the most accurate WtP models will need ~3.5
GB of GPU memory. SaT is the newer successor to WtP from the same authors and
generally offers better accuracy/efficiency.

On the other hand, spaCy has a single multilingual sentence detection
that appears to work better for splitting up English text in certain cases.

This component has been updated to use the Azure Translation Component's NewLineBehavior class
for swapping newlines with either whitespace or removing it altogether based on script detected.

The reason why we need to consider the script/character encodings is because certain languages
will treat whitespace between words as possessing different meanings. For instance in Chinese

`电脑` would mean `computer` but `电 脑` would mean `electricity brain`.

When calling the NLP text splitter, users can adjust the following parameters to control for sentence
splitting behaviors:

- `split_mode`: set to `DEFAULT` for splitting by chunk size and `SENTENCE` when splitting by sentences

- `newline_behavior` : controls how newlines are handled in a submitted input text. Options include:
  - `GUESS`  to choose ' ' for space-separated langs; '' for Chinese/Japanese/Korean.
  - `SPACE`  to always replace with a single space.
  - `REMOVE` to always remove (no space).
  - `NONE`   to no change.
  By default, the newline behavior will attempt to guess whether to swap newlines with spaces or remove entirely.

- `limit` :  The max size cutoff for a given text split.
- `preferred_limit` : A soft target size for chunking. If set > 0 and less than the hard limit, the splitter
                      will try to create chunks near this size while still respecting the hard limit.
                      Disabled by default when set to -1.

  Depending on the component, the preferred_limit would not be required or optimal. For instance Azure services/components typically have a batch limit of around 50,000 characters for a single job, with no need for a soft text limit to perform effective translation.


For instance:
```
    result = list(TextSplitter.split(input_text,
                  ...
                  self.sat_model,
                  split_mode='DEFAULT')
                  newline_behavior='NONE',
                  limit = 50000,
                  preferred_limit = 25000)
```
Will attempt to split using an SaT model, using the default chunking parameters and no newline adjustments. The given text chunks
would ideally be around 25,000 characters (or tokens, depending on the text size function provided) but can in some cases reach 50,000
if the text splitter is unable to identify a proper split at the lower preferred limit.




# Installation

To install this tool users will need to run `./install.sh`. By default this will set up a
CPU-only PyTorch installation. `./install.sh` requires a C++ compiler and the Python development
headers to be installed. If they are not already installed, they can be installed by running
`apt-get install g++ python3.12-dev`.

Please note that several customizations are supported:

- `--text-splitter-dir|-t <path_to_src>`: This parameter specifies where the
  source code is located relative to the installation script. In general,
  since the installation script and source code are both located here, it's not
  necessary to update this parameter unless the user is running the `install.sh`
  script from a different directory.

- `--gpu`: Add this parameter to the installation command line above to
  setup a PyTorch installation with CUDA (GPU) libraries.

- `--wtp-models-dir |-m <wtp-models-dir >`: Add this parameter to
  change the default WtP/SaT model installation directory
  (default: `/opt/wtp/models`).

- `--install-wtp-model|-w <model-name>`: Add this parameter to specify
  additional WtP/SaT models for installation. Accepts both WtP names
  (e.g., `wtp-bert-mini`) and SaT names (e.g., `sat-6l-sm`).
  This parameter can be provided multiple times to install more than one model.

- `--install-spacy-model|-s <model-name>`: Add this parameter to specify
  additional spaCy models for installation. This parameter can be provided
  multiple times to install more than one model.


# Optimal WtP / SaT model:

Based on testing, `sat-6l-sm` emerges as the recommended model, particularly when accuracy is prioritized and GPU resources (~1 GB) are available

| Metric                   | sat-3l-sm       | sat-6l-sm       | Difference               |
|--------------------------|-----------------|-----------------|--------------------------|
| **Accuracy (%)**         | 97.6%           | **98.8%**       | +1.2%                    |
| **GPU Memory Used (MB)** | **1083.8**      | 1125.8          | +42 MB (~4% increase)    |
| **GPU Processing Time (s)**  | **2.81**    | 3.00            | +0.19 s                  |
| **CPU Processing Time (s)**  | **6.57**    | 11.72           | **+5.15 s (significant)**|

Key Considerations:
- `sat-3l-sm` is slightly less accurate but runs at x2 speedup in CPU compared to `sat-6l-sm`
- While running on GPU: Both models use roughly the same amount of GPU resource/runtime.
- This means that it's generally advantageous to use `sat-6l-sm` when GPU is available, and to fall back to `sat-3l-sm` if only CPU resources are available.

For detailed results and additional models, see [WtP SaT Text Splitter Analysis](WtP%20SaT%20Text%20Splitter%20Analysis.xlsx).
