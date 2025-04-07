# Agile Mind

## Overview

Agile Mind is an AI-powered development platform that builds software repositories from natural language descriptions. It uses a LLM-based multi-agent architecture to automate the software development process, from requirements gathering to code generation and documentation.

## Features

- **Multi-Agent Architecture**: Specialized AI agents for different development tasks
- **Code Generation**: Automated creation of code from requirements or descriptions
- **Collaborative Development**: Agents can work together to solve complex programming challenges
- **Documentation**: AI-generated documentation that stays in sync with code
- **Checking**: Automated code review and static analysis

## Online visualization

Check out the online visualization of AgileMind!

> Note that the online version does not support human-agent interaction and parallel processing yet. Consider using the command line version for those features.

### Usage

```bash
git clone https://github.com/wnrock/AgileMind.git
cd AgileMind

pip install -r requirements.txt

streamlit run web.py
```

## Quick Start

### Set Up Environment Variables

#### 1. Use `.env` file

```bash
cp .env.template .env
# Then replace the placeholder values with actual credentials
```

#### 2. Set environment variables manually

```bash
export OPENAI_API_KEY="<Your_API_key>"
export OPENAI_BASE_URL="<Your_OpenAI_API_base_url>" # Optional
```

#### 3. Pass as command-line arguments

Currently only supported for Docker. Check the Docker section below.

### Get Started

#### 1. From PyPI

```bash
pip install AgileMind

agilemind "Create a 2048 game with UI" -o output
```

#### 2. Docker

```bash
docker run -it                                      \
    -e OPENAI_API_KEY="<Your_API_key>"              \
    -e OPENAI_BASE_URL="<Your_OpenAI_API_base_url>" \
    -v <Your_output_dir>:/agilemind/output          \
    ghcr.io/wnrock/agilemind:latest                 \
    "Create a 2048 game with UI"                    \
    -o output
```

#### 3. From source

```bash
git clone https://github.com/wnrock/AgileMind.git
cd AgileMind

pip install -r requirements.txt

python app.py "Create a 2048 game with UI" -o output
```
