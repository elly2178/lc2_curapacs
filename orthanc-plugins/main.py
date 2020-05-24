import sys
import json
import requests
import multiprocessing
from curapacs_python import config
from curapacs_python.OrthancHost import OrthancHost

try:
    import orthanc
except ImportError:
    config.LOGGER.warning("Failed to import orthanc module.")

def enhance_query(output, uri_path, **kwargs):
    config.LOGGER.debug(f"{uri_path} called with body: {kwargs['body']}")
    local_orthanc = OrthancHost(f"http://localhost:{config.LOCAL_HTTP_PORT}",
                            http_user=config.LOCAL_HTTP_USER,
                            http_password=config.LOCAL_HTTP_PASSWORD)
    remote_orthanc = OrthancHost(config.PEER_URI,
                             http_user=config.PEER_HTTP_USER,
                             http_password=config.PEER_HTTP_PASSWORD)

    request_body_dict = local_orthanc.getDictFromRequestBody(kwargs["body"])
    config.LOGGER.debug(f"Request body decoded to: {request_body_dict}")

    find_level = OrthancHost.getQueryRetrieveLevel(request_body_dict)
    find_query = OrthancHost.collateFindQuery(request_body_dict)

    #Search for resources via Orthanc API (remote), store all resources found in list
    try:
        remote_resources = []
        remote_orthanc_resources_found = remote_orthanc.findResources(find_query, find_level)
    except (requests.ConnectTimeout, requests.ConnectionError):
        config.LOGGER.error(f"Failed to connect to {remote_orthanc.url} to query for resources.")
    else:
        for resource in remote_orthanc_resources_found:
            resource_list = remote_orthanc.getSubresourcesOfOrthancResource(resource, find_level)
            config.LOGGER.debug(f"Resources found for remote resource: {resource_list}")
            remote_resources.extend(resource_list)

    #Search for resources via Orthanc API (local), store all resources found in list
    local_orthanc_resources_found = local_orthanc.findResources(find_query, find_level)
    local_resources = []
    for resource in local_orthanc_resources_found:
        resource_list = local_orthanc.getSubresourcesOfOrthancResource(resource, find_level)
        config.LOGGER.debug(f"Resources found for local resource: {resource_list}")
        local_resources.extend(resource_list)


    remote_ids = [OrthancHost.getIDOfResource(resource) for resource in remote_resources]
    local_ids = [OrthancHost.getIDOfResource(resource) for resource in local_resources]
    strictly_remote_ids = set(remote_ids) - set(local_ids)
    strictly_local_ids = set(local_ids) - set(remote_ids)
    intersecting_ids = set(local_ids) & set(remote_ids)
    config.LOGGER.debug(f"Required resources not present on local orthanc are: {strictly_remote_ids}")
    config.LOGGER.debug(f"Resources present on both local and remote ortanc are: {strictly_local_ids}")
    config.LOGGER.debug(f"Resources present on both local and remote ortanc are: {intersecting_ids}")

    #Collate dictionaries (numeric dicom tags / dicom values) for every resource found
    dicom_list = []
    try:
        for resource_id in strictly_remote_ids:
            resource = OrthancHost.getResourceByID(remote_resources, resource_id)
            dicom_dict = remote_orthanc.getTagsAndValuesOfOrthancResource(resource_id, find_level)
            dicom_list.append(OrthancHost.filterTagsOfDicomDict(dicom_dict, find_query, find_level))
    except (requests.ConnectTimeout, requests.ConnectionError):
        config.LOGGER.error(f"Failed to connect to {remote_orthanc.url} to get dicom data for instances.")

    for resource_id in strictly_local_ids | intersecting_ids:
        resource = OrthancHost.getResourceByID(local_resources, resource_id)
        dicom_dict = local_orthanc.getTagsAndValuesOfOrthancResource(resource_id, find_level)
        dicom_list.append(OrthancHost.filterTagsOfDicomDict(dicom_dict, find_query, find_level))

    dicom_list_as_json = json.dumps(dicom_list)
    config.LOGGER.debug(f"Returning list of dicom dicts to caller: {dicom_list_as_json}")

    if output is not None:
        output.AnswerBuffer(dicom_list_as_json, 'application/json')

def enhance_c_move():
    pass

def orthanc_websocket():
    import time
    counter = 0
    while True:
        config.LOGGER.debug("COUNTER IS AT " + str(counter))
        time.sleep(5)
        counter += 1

def on_change(changeType, level, resource):
    orthanc_websocket_process = multiprocessing.Process(target=orthanc_websocket)
    orthanc_websocket_process.daemon = True
    if changeType == orthanc.ChangeType.NEW_INSTANCE:
        body = json.dumps({"Resources": [resource], "Asynchronous": True})
        config.LOGGER.debug(f"Change Callback started, type: {changeType}, body: {body}")
        config.LOGGER.debug(f"Uploading instance {resource} to peer {config.PEER_NAME}")
        result = orthanc.RestApiPost(f"/peers/{config.PEER_NAME}/store", body)
        result_dict = json.loads(result.decode())
        config.LOGGER.debug(f"Orthanc job with ID {result_dict['ID']} started.")
    if changeType == orthanc.ChangeType.ORTHANC_STARTED:
        orthanc_websocket_process.start()
    if changeType == orthanc.ChangeType.ORTHANC_STOPPED:
        orthanc_websocket_process.terminate()


if "orthanc" in sys.modules:
    orthanc.RegisterRestCallback('/enhancequery', enhance_query)
    orthanc.RegisterOnChangeCallback(on_change)
