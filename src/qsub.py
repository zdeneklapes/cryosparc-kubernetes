#!/usr/bin/python3
import string
import random
from os import path
import shlex
import json
from pprint import pprint
import yaml

from kubernetes import client, config
from kubernetes.client.models import V1Job
from argparse import ArgumentParser, Namespace


def get_command_output(response: V1Job, args: Namespace) -> str:
    """Source: https://stackoverflow.com/a/58848906/14471542"""
    core_v1 = client.CoreV1Api()
    pod_label_selector = "controller-uid=" + response.metadata.labels['controller-uid']
    pods_list = core_v1.list_namespaced_pod(
        namespace=args.namespace, label_selector=pod_label_selector, timeout_seconds=10
    )

    # Notice that:
    # - there are more parameters to limit size, lines, and more - see
    #   https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CoreV1Api.md#read_namespaced_pod_log
    # - the logs of the 1st pod are returned (similar to `kubectl logs job/<job-name>`)
    # - assumes 1 container in the pod
    pod_name = pods_list.items[0].metadata.name
    try:
        # For whatever reason the response returns only the first few characters unless
        # the call is for `_return_http_data_only=True, _preload_content=False`
        pod_log_response = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=args.namespace,
            _return_http_data_only=True,
            _preload_content=False
        )
        pod_log = pod_log_response.data.decode("utf-8")
        return pod_log.strip()
    except client.rest.ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)


def delete_none(_dict):
    """
    Delete None values recursively from all of the dictionaries
    Source: https://stackoverflow.com/a/66127889/14471542
    """
    for key, value in list(_dict.items()):
        if isinstance(value, dict):
            delete_none(value)
        elif value is None:
            del _dict[key]
        elif isinstance(value, list):
            for v_i in value:
                if isinstance(v_i, dict):
                    delete_none(v_i)

    return _dict


def transform_dict(data):
    """
    Transform dictionary keys from snake_case to camelCase
    :param data:
    :return:
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = ''.join(word.capitalize() for word in key.split('_'))
            new_key = new_key[0].lower() + new_key[1:]
            new_dict[new_key] = transform_dict(value)
        return new_dict
    elif isinstance(data, list):
        return [transform_dict(item) for item in data]
    else:
        return data


def create_job_object(args: Namespace):
    # Configurate Pod template container
    command = shlex.split(args.run_cmd)
    container = client.V1Container(
        name=args.job_name,
        image=args.image,
        command=command,
        security_context=client.V1SecurityContext(
            run_as_user=1000,
            run_as_group=1000,
        ),
        resources=client.V1ResourceRequirements(
            requests={"cpu": args.num_cpu, "memory": args.memory},
            limits={"cpu": args.num_cpu, "memory": args.memory, "nvidia.com/gpu": args.num_gpu},
        ),
        # TODO
        # volume_mounts=[
        #     client.V1VolumeMount(
        #         name="vol-1",
        #         mount_path="/mnt/data"
        #     )
        # ]
    )
    volumes = [
        # TODO
        # client.V1Volume(
        #     name="vol-1",
        #     persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
        #         claim_name="pvc-data"
        #     )
        # )
    ]
    # Create and configure a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": args.job_name}),
        spec=client.V1PodSpec(restart_policy="Never", containers=[container], volumes=volumes),
    )
    # Create the specification of deployment
    spec = client.V1JobSpec(
        template=template,
        backoff_limit=4
    )
    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=args.job_name),
        spec=spec
    )
    return job


def create_job(api_instance, job, args: Namespace):
    try:
        api_response: V1Job = api_instance.create_namespaced_job(
            body=job,
            namespace=args.namespace,
        )
        print(f"{api_response.metadata.name}")
    except client.rest.ApiException as e:
        print("[FAILED] Can not create: Status=%s : JobName=%s : Reason=%s" % (
        e.status, args.job_name, eval(e.body)['reason']))
        pprint(eval(e.body))
        pprint(e.headers)
        exit(1)


def parse_arguments():
    args = ArgumentParser()

    # Required
    args.add_argument("--run-cmd", type=str, required=True, help="Command to run in container")

    # Optional
    args.add_argument(
        '--job-name',
        type=str,
        default=''.join(random.choices(string.ascii_lowercase + string.digits, k=7)),
        help="Name of the job"
    )  # TODO: Check if job already exists, if so, generate new name
    args.add_argument('--namespace', type=str, default="default", help="Name of the job")
    args.add_argument("--image", type=str, default="busybox:1.28", help="Container image to use")
    args.add_argument("--num-cpu", type=str, default="1", help="Number of CPU cores to use")
    args.add_argument("--num-gpu", type=str, default=0, help="Number of GPU cores to use")
    args.add_argument("--memory", type=str, default="10Mi", help="Memory to use")
    args.add_argument("--walltime", type=str, default="02:00:00", help="Walltime")
    args.add_argument("--scratch-local", type=str, default="1000Mi", help="Number of GPU cores to use")
    args.add_argument("--command", type=str, help="Command to run in container")
    args.add_argument("--script-path-abs", type=str, help="Command to run in container")
    args.add_argument("--cluster-job-id", type=str, help="Command to run in container")
    args.add_argument("--src-path", type=str, help="Command to run in container")
    args.add_argument("--dest-path", type=str, help="Command to run in container")
    args.add_argument("--project-uid", type=str, help="Command to run in container")
    args.add_argument("--job-uid", type=str, help="Command to run in container")
    args.add_argument("--output", type=str, nargs="*", default=[], help="Output file")
    args.add_argument("--local-config", action="store_true", default=False, help="Local config")
    args.add_argument("-d", action="store_true", help="Debug mode")
    return args.parse_args()


def main():
    args = parse_arguments()
    if len(args.job_name) == 0:
        args.job_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))

    if args.d:
        print("pi [CREATED]")
        exit(0)

    if args.local_config:
        config.load_kube_config()
    else:
        config.load_incluster_config()
    batch_v1 = client.BatchV1Api()
    job = create_job_object(args)

    if "yaml" in args.output:
        with open(path.join(path.dirname(__file__), "job.yaml"), "w") as f:
            yaml.dump(transform_dict(delete_none(job.to_dict())), f)

    if "json" in args.output:
        with open(path.join(path.dirname(__file__), "job.json"), "w") as f:
            json.dump(job.to_dict(), f)

    try:
        create_job(batch_v1, job, args)
    except client.rest.ApiException as e:
        print("Exception when calling BatchV1Api->create_namespaced_job: %s" % e)


if __name__ == '__main__':
    main()
