FROM docker.io/python:3.7

RUN useradd --user-group --create-home --no-log-init --shell /bin/nologin --uid 1001 gunicorn

WORKDIR /tmp
RUN apt-get upgrade -y && \
    apt-get update -y && \
    apt-get install -y apt-transport-https gnupg2 && \
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list && \
    apt-get update -y && \
    apt-get install -y kubectl && \
    wget 'https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv3.6.1/kustomize_v3.6.1_linux_amd64.tar.gz' -O kustomize.tgz && \
    tar -xzf kustomize.tgz && \
    cp kustomize /usr/bin/ && \
    chmod 755 /usr/bin/kustomize && \
    rm -f kustomize kustomize.tgz && \
    pip install --no-cache-dir flask_restful gunicorn kubernetes

USER gunicorn
CMD [ "gunicorn", "/opt/provisioner/provisioner/run:app" ]
