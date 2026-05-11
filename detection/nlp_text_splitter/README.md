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

This utility includes a `NewLineBehavior` helper for swapping single newlines with either whitespace or removing them altogether based on script detected.

The reason why we need to consider the script/character encodings is because certain languages
will treat whitespace between words as possessing different meanings. For instance in Chinese

`电脑` would mean `computer` but `电 脑` would mean `electricity brain`.

When calling the NLP text splitter, users can adjust the following parameters to control for sentence
splitting behaviors:

- `split_mode`: set to `DEFAULT` for splitting by chunk size and `SENTENCE` when splitting by sentences

- `newline_behavior` : controls how single newlines are handled in a submitted input text. Options include:
  - `GUESS`  to choose ' ' for space-separated langs; '' for Chinese/Japanese/Korean.
  - `SPACE`  to always replace with a single space.
  - `REMOVE` to always remove (no space).
  - `NONE`   to no change.
  By default, the newline behavior will attempt to guess whether to swap newlines with spaces or remove entirely.
  Note that newlines that exist next to other newlines or whitespace are ignored.

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

## Edge case: mid-word splits

In most cases, the text splitter should be able to identify an appropriate sentence break, especially when sufficient text is available.

However, if a single sentence is long enough that the configured limit falls in the middle of an alphanumeric sequence, the splitter uses the following best-effort heuristic:

1. Detect that the split point falls between two alphanumeric characters.
2. Attempt to backtrack to the nearest whitespace character.
3. Split at that whitespace and continue processing.

If no whitespace can be found, the splitter will fall back to a mid-word / mid-token split so that progress can still be made.

Please note that this is only a heuristic. Punctuation-delimited values such as `1,000` or `1.0` may still split at punctuation boundaries, and languages that do not normally use whitespace may still require character-level splits in some cases.


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

| Metric                   | sat-3l-sm       | sat-6l-sm       | Difference                 |
|--------------------------|-----------------|-----------------|----------------------------|
| **Accuracy (%)**         | 97.6%           | **98.8%**       | +1.2%                      |
| **GPU Memory Used (MB)** | **1083.8**      | 1125.8          | +42 MB (~4% increase)      |
| **GPU Processing Time (s)**  | **2.81**    | 3.00            | +0.19 s                    |
| **CPU Processing Time (s)**  | **6.57**    | 11.72           | **+5.15 s (~78% increase)**|

Key Considerations:
- `sat-3l-sm` is slightly less accurate but runs at x2 speedup in CPU compared to `sat-6l-sm`
- While running on GPU: Both models use roughly the same amount of GPU resource/runtime.
- This means that it's generally advantageous to use `sat-6l-sm` when GPU is available, and to fall back to `sat-3l-sm` if only CPU resources are available.

## Test Data

The MPF team created a small set of synthetic benchmarks for evaluating the text splitter models.

The benchmarks were designed to cover several categories of sentence-splitting behavior, including:

- Short explicit edge cases in English and German
- Titles, abbreviations, numbering, and numeric forms
- Lorem-Ipsum English passages built from a randomized pool of everyday English sentences.
- Multilingual passages in English, Chinese, Russian, Spanish, and Arabic
- Multilingual passages created by shuffling and mixing sentences from different languages.

In total, the analysis evaluated 85 tests across these categories. Users who want to inspect the exact passages and model outputs can review the `Model Predictions` tab in [WtP SaT Text Splitter Analysis](WtP%20SaT%20Text%20Splitter%20Analysis.xlsx), as well as review overall stats for each model tested.
