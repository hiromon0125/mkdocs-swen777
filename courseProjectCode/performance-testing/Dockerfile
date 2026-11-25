FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /source
COPY courseProjectCode/performance-testing/requirements.txt /bench/requirements.txt
RUN pip install --no-cache-dir -r /bench/requirements.txt
COPY pyproject.toml hatch_build.py README.md ./
COPY mkdocs ./mkdocs
RUN pip install --no-cache-dir --no-deps --no-build-isolation .
COPY courseProjectCode/performance-testing/ /bench/
RUN python /bench/fixture.py /fixture && pip freeze > /bench/environment.txt
WORKDIR /bench
CMD ["python", "run.py", "--help"]
