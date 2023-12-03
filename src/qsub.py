#!/usr/bin/python3
import string
import random
from os import path
import json
from pprint import pprint
import yaml
import re

from kubernetes import client, config
from kubernetes.client.models import V1Job
from argparse import ArgumentParser, Namespace
# from logging import getLogger
import logging

# set logger to file /tmp/cryosparc.log
logging.basicConfig(filename='/tmp/cryosparc.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logging.info("Running Urban Planning")
logger = logging.getLogger('urbanGUI')


def get_command_output(response: V1Job, args: Namespace) -> str:
    """Source: https://stackoverflow.com/a/58848906/14471542"""
    core_v1 = client.CoreV1Api()
    pod_label_selector = "controller-uid=" + response.metadata.labels['controller-uid']
    pods_list = core_v1.list_namespaced_pod(
        namespace=args.namespace,
        label_selector=pod_label_selector,
        timeout_seconds=10
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


def create_service_object(args: Namespace):
    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=args.job_name),
        spec=client.V1ServiceSpec(
            type="ClusterIP",  # default
            # type="NodePort", # Ports: 30000-32767; Don't need it here, to access nodePort; Extension of ClusterIP
            # type="LoadBalancer", # Extension of NodePort
            cluster_ip="None",
            selector={"app": args.job_name},
            ports=[client.V1ServicePort(
                port=80,
                target_port=8080
            )]
        )
    )
    return service


def create_job_object(args: Namespace):
    # Configurate Pod template container
    interpreter = "/bin/bash"
    worker_connect_cmd = f"/opt/cryosparc_worker/bin/cryosparcw connect --worker {args.job_name} --master {args.master_hostname} --port {args.master_port} --ssdpath {args.ssd_path}"
    run_cmd = args.run_cmd
    command = f"{worker_connect_cmd} && {interpreter} {run_cmd}"
    # command = f"{interpreter} {run_cmd}"
    print(f"{interpreter} -c \"{command}\"")
    exit(0)
    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=args.job_name),
        spec=client.V1JobSpec(
            backoff_limit=0,  # TODO: What is the correct value?
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": args.job_name}),
                spec=client.V1PodSpec(
                    restart_policy="Never",
                    containers=[
                        client.V1Container(
                            name=args.job_name,
                            image=args.image,
                            command=[interpreter],
                            args=["-c", command],
                            security_context=client.V1SecurityContext(
                                run_as_user=1000,
                                run_as_group=1000,
                                allow_privilege_escalation=False,
                                capabilities=client.V1Capabilities(
                                    drop=["ALL"]
                                ),
                            ),
                            env=[
                                client.V1EnvVar(
                                    name="USER",
                                    value="cryo"
                                ),
                                # client.V1EnvVar(
                                #     name="USER",
                                #     value_from=client.V1EnvVarSource(
                                #         secret_key_ref=client.V1SecretKeySelector(
                                #             name="cryosparc-secret",
                                #             key="CRYOSPARC_LICENSE_ID"
                                #         )
                                #     )
                                # ),
                            ],
                            resources=client.V1ResourceRequirements(
                                requests={"cpu": args.num_cpu, "memory": args.memory},
                                limits={
                                    "cpu": args.num_cpu,
                                    "memory": args.memory,
                                    args.name_gpu: args.num_gpu,
                                }
                            ),
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="cryosparc-volume-1",
                                    mount_path="/mnt"
                                )
                            ]
                        )
                    ],
                    volumes=[
                        client.V1Volume(
                            name="cryosparc-volume-1",
                            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                claim_name="pvc-cryosparc-scratch"
                            )
                        )
                    ],
                    security_context=client.V1PodSecurityContext(
                        # Pod security context
                        fs_group_change_policy="OnRootMismatch",
                        run_as_non_root=True,
                        seccomp_profile=client.V1SeccompProfile(
                            type="RuntimeDefault"
                        ),
                    )
                ),
            ),
        ),
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


def create_service(api_instance, service, args: Namespace):
    try:
        api_response = api_instance.create_namespaced_service(
            body=service,
            namespace=args.namespace,
        )
        print(f"{api_response.metadata.name}")
    except client.rest.ApiException as e:
        print("Exception when calling CoreV1Api->create_namespaced_service: %s\n" % e)


def parse_arguments():
    args = ArgumentParser()

    # Required
    args.add_argument("--run-cmd", type=str, required=True, help="Command to run in container")

    # Optional
    args.add_argument(
        '--job-name',
        type=str,
        default=None,
        # default=''.join(random.choices(string.ascii_lowercase + string.digits, k=7)),
        help="Name of the job"
    )
    args.add_argument('--namespace', type=str, default="default", help="Name of the job")
    args.add_argument(
        "--image",
        type=str,
        # default="cerit.io/cerit/cryosparc:master-v0.2",
        default="cerit.io/cerit/cryosparc:worker-v0.2",
        help="Image name"
    )

    args.add_argument(
        '--name-gpu', type=str,
        # default="nvidia.com/gpu",
        default="nvidia.com/mig-1g.10gb",
        help="Name of the GPU resource"
    )

    args.add_argument("--master-port", type=int, default=8080, help="Number of CPU cores to use")
    args.add_argument("--master-hostname", type=str, default="cryosparc-service", help="Number of CPU cores to use")
    args.add_argument("--ssd-path", type=str, default="/mnt", help="Where to store data")
    args.add_argument("--num-cpu", type=int, default=1, help="Number of CPU cores to use")
    args.add_argument("--num-gpu", type=int, default=1, help="Number of GPU cores to use")
    args.add_argument("--memory", type=str, default="10Gi", help="Memory to use")
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
    _args = args.parse_args()

    if _args.job_name == "" or _args.job_name is None or _args.job_name.startswith("-"):
        # print("Generating random job name")
        _args.job_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
        # TODO: Check if job already exists, if so, generate new name
    else:
        _args.job_name = _args.job_name.lower()

    # validate job_name; regex: "[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*')"
    regex = re.compile("[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*")
    if not regex.match(_args.job_name):
        print("Job name is invalid. Job name must match regex: %s" % regex.pattern)
        exit(1)

    # print(_args.job_name)
    logger.debug(_args)
    logger.debug("aaa")
    logger.info("aaa")
    return _args


def main():
    args = parse_arguments()

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
        # create_service(batch_v1, create_service_object(args), args)
        create_job(batch_v1, job, args)
    except client.rest.ApiException as e:
        print("Exception when calling BatchV1Api->create_namespaced_job: %s" % e)


if __name__ == '__main__':
    main()
