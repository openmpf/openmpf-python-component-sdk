# OpenMPF Python Component SDK

Welcome to the Open Media Processing Framework (OpenMPF) Python Component SDK Project!

## What is the OpenMPF?

OpenMPF provides a platform to perform content detection and extraction on bulk multimedia, enabling users to analyze, search, and share information through the extraction of objects, keywords, thumbnails, and other contextual data.

OpenMPF enables users to build configurable media processing pipelines, enabling the rapid development and deployment of analytic algorithms and large-scale media processing applications.

### Search and Share

Simplify large-scale media processing and enable the extraction of meaningful content

### Open API

Apply cutting-edge algorithms such as face detection and object classification

### Flexible Architecture

Integrate into your existing environment or use OpenMPF as a standalone application

## Overview

This repository contains source code for the Open Media Processing Framework (OpenMPF) Python Component SDK, including the API and associated utilities.

In OpenMPF, a  **component**  is a plugin that receives jobs (containing media), processes that media, and returns results.

Using this API, detection components can be built to provide:

- Detection (Localizing an object)
- Tracking (Localizing an object across multiple frames)
- Classification (Detecting the type of object and optionally localizing that object)
- Transcription (Detecting speech and transcribing it into text)

## Where Am I?

- [Parent OpenMPF Project](https://github.com/openmpf/openmpf-projects)
- [OpenMPF Core](https://github.com/openmpf/openmpf)
- Components
    * [OpenMPF Standard Components](https://github.com/openmpf/openmpf-components)
    * [OpenMPF Contributed Components](https://github.com/openmpf/openmpf-contrib-components)
- Component APIs:
    * [OpenMPF C++ Component SDK](https://github.com/openmpf/openmpf-cpp-component-sdk)
    * [OpenMPF Java Component SDK](https://github.com/openmpf/openmpf-java-component-sdk)
    * [OpenMPF Python Component SDK](https://github.com/openmpf/openmpf-python-component-sdk) ( **You are here** )
- [OpenMPF Build Tools](https://github.com/openmpf/openmpf-build-tools)
- [OpenMPF Web Site Source](https://github.com/openmpf/openmpf.github.io)
- [OpenMPF Docker](https://github.com/openmpf/openmpf-docker)

## Getting Started

### Build and Install the Component SDK
* If not already installed, 
  [build and install Python 3.8.](https://openmpf.github.io/docs/site/Development-Environment-Guide#python-38)
* Install the Python Component API: `pip3 install openmpf-python-component-sdk/detection/api`
* (Optional) Install the Python Component Utilities: `pip3 install openmpf-python-component-sdk/detection/component_util`

### Using the Component SDK

Please read the 
[Python Batch Component API documentation](https://openmpf.github.io/docs/site/Python-Batch-Component-API) 
to get started.

## Project Website

For more information about OpenMPF, including documentation, guides, and other material, visit our 
[website](https://openmpf.github.io/).

## Project Workboard

For a latest snapshot of what tasks are being worked on, what's available to pick up, and where the project stands as a whole, check out our [workboard](https://github.com/orgs/openmpf/projects/11).

