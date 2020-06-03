import config as provisioner_config

class APIResponseParser:
    """
    So responses are being handled uniform
    """
    def __init__(self, response):
        self.response = response
        self.api_version = response.api_version
        self.kind = response.kind
    
    def parse(self):
        if self.api_version == "v1":
            if self.kind == "PodList":
                return PodListParser(self.response)

class PodListParser:
    def __init__(self, response):
        self.response = response

    def get_pod_list(self):
        return [{"pod_ip": pod.status.pod_ip,
                 "namespace": pod.metadata.namespace,
                 "name": pod.metadata.name,
                 "labels": pod.metadata.labels} for pod in self.response.items]
