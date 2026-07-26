ARG BASE_IMAGE
FROM ${BASE_IMAGE}

COPY oci_fixture.py /opt/llm-wiki/oci-fixture
RUN chmod 0555 /opt/llm-wiki/oci-fixture \
    && mkdir -p /llm-wiki/input /llm-wiki/output \
    && touch /llm-wiki/input/packet.json \
        /llm-wiki/input/probe-request.json \
        /llm-wiki/output/result.json \
        /llm-wiki/output/probe-result.json

USER 65532:65532
ENTRYPOINT ["/opt/llm-wiki/oci-fixture"]
