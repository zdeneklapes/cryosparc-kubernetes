# Copyright 2016 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Creates, updates, and deletes a job object.
"""

from os import path
from time import sleep
from argparse import ArgumentParser, Namespace
import yaml
from typing import Optional
from dataclasses import dataclass, fields
import shlex

from kubernetes import client, config

from utils import delete_none, transform_dict


@dataclass
class Program:
    args: Namespace
    api_instance: client.BatchV1Api
    job: Optional[client.V1Job] = None


def create_job_object(args: Namespace):
    # Configureate Pod template container
    cmd = shlex.split(args.run_cmd)
    container = client.V1Container(
        name=args.job_name,
        image=args.image,
        command=cmd,
    )
    # Create and configure a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": args.app_name}),
        spec=client.V1PodSpec(restart_policy="Never", containers=[container]))
    # Create the specification of deployment
    spec = client.V1JobSpec(
        template=template,
        backoff_limit=4)
    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=args.job_name),
        spec=spec)

    return job


def create_job(program: Program):
    api_response = program.api_instance.create_namespaced_job(
        body=program.job,
        namespace="default")
    print("Job created. status='%s'" % str(api_response.status))
    get_job_status(program)


def get_job_status(program: Program):
    job_completed = False
    while not job_completed:
        api_response = program.api_instance.read_namespaced_job_status(
            name=program.args.job_name,
            namespace="default"
        )
        if api_response.status.succeeded is not None or api_response.status.failed is not None:
            job_completed = True
        print("Job status='%s'" % str(api_response.status))


def update_job(program: Program):
    # Update container image
    program.job.spec.template.spec.containers[0].image = "perl"
    api_response = program.api_instance.patch_namespaced_job(
        name=program.args.job_name,
        namespace="default",
        body=program.job
    )
    print("Job updated. status='%s'" % str(api_response.status))


def delete_job(program: Program):
    api_response = program.api_instance.delete_namespaced_job(
        name=program.args.job_name,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5
        )
    )
    print("Job deleted. status='%s'" % str(api_response.status))


def parse_arguments():
    args = ArgumentParser()
    args.add_argument("--app-name", type=str, help="Name of the application")
    args.add_argument('--job-name', type=str, help="Name of the job")
    args.add_argument("--image", type=str, help="Container image to use")
    args.add_argument("--run-cmd", type=str, help="Command to run in container")
    args.add_argument("--num-cpu", type=int, help="Number of CPU cores to use")
    args.add_argument("--num-gpu", type=int, help="Number of GPU cores to use")
    return args.parse_args()


def main():
    program = Program(
        args=parse_arguments(),
        api_instance=client.BatchV1Api()
    )
    config.load_kube_config()
    program.job = create_job_object(program.args)

    # Dump
    dict_to_yaml = transform_dict(delete_none(program.job.to_dict()))
    yaml.dump(dict_to_yaml, open(path.join(path.dirname(__file__), "job-foo.yaml"), "w"))


    create_job(program)
    update_job(program)
    delete_job(program)


if __name__ == '__main__':
    main()
