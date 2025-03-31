# Agile Mind

## Overview

Agile Mind is an AI-powered development platform that builds software repositories from natural language descriptions. It uses a multi-agent architecture to automate the software development process, from requirements gathering to code generation and documentation.

## Features

- **Multi-Agent Architecture**: Specialized AI agents for different development tasks
- **Code Generation**: Automated creation of code from requirements or descriptions
- **Collaborative Development**: Agents can work together to solve complex programming challenges
- **Documentation**: AI-generated documentation that stays in sync with code
- **Checking**: Automated code review and static analysis

## Getting Started

```bash
# Clone the repository
git clone https://github.com/wnrock/AgileMind.git
cd AgileMind

# Install dependencies
pip install -r requirements.txt

# Prepare environment variables
cp .env.template .env # Then replace the placeholder values with actual credentials
# Or set environment variables manually: OPENAI_API_KEY, OPENAI_BASE_URL, etc.

# Start developing
python app.py "Create a 2048 game with UI" -o output
```
