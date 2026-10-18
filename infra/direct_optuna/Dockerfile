FROM vllm/vllm-openai@sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14
ARG UPSTREAM_COMMIT=bc856d4cad5f14d83b1bd284fbd7187d75c8c496
RUN git clone https://github.com/InseeFrLab/auto-tuning-vllm.git /opt/auto-tuning-vllm \
    && git -C /opt/auto-tuning-vllm checkout "$UPSTREAM_COMMIT" \
    && uv venv --system-site-packages --seed --python /usr/bin/python3 /opt/tune-env
COPY requirements.txt /tmp/benchmark-requirements.txt
RUN /opt/tune-env/bin/pip install -r /tmp/benchmark-requirements.txt \
    && /opt/tune-env/bin/pip install --no-deps -e /opt/auto-tuning-vllm
# vLLM subprocesses must retain the pinned image's original Python environment.
ENV PATH=/usr/local/bin:/usr/bin:/bin:/opt/tune-env/bin
ENTRYPOINT ["/opt/tune-env/bin/python"]
