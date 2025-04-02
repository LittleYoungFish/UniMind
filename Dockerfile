FROM python:3.12.3-slim

# Set the working directory
WORKDIR /agilemind

# Copy the current directory contents into the container
COPY . .

# If "pip_mirror" is set, use pip mirror
ARG pip_mirror=False
RUN if [ "$pip_mirror" = "True" ]; then pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple; fi

# Install needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set entrypoint
ENTRYPOINT ["python", "app.py"]
