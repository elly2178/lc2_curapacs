FROM docker.io/python:3.7

WORKDIR /tmp
RUN apt-get upgrade -y && \
    apt-get update -y && \
    wget 'https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv3.6.1/kustomize_v3.6.1_linux_amd64.tar.gz' -O kustomize.tgz && \
    tar -xzf kustomize.tgz && \
    cp kustomize /usr/bin/ && \
    chmod 755 /usr/bin/kustomize && \
    rm -f kustomize kustomize.tgz && \
    pip install --no-cache-dir flask_restful gunicorn kubernetes
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0"
CMD [ "gunicorn", "/opt/provisioner/run.py:main()" ]
