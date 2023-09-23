#!/usr/bin/python3
from pprint import pprint

from kubernetes import client, config
from argparse import ArgumentParser, Namespace

# TODO: Printing this info about job:
"""
cerit-pbs.cerit-sc.cz:
Req'd  Req'd   Elap
Job ID               Username Queue    Jobname    SessID NDS TSK Memory Time  S Time
-------------------- -------- -------- ---------- ------ --- --- ------ ----- - -----
5612883.cerit-pbs.c* zdenekl* q_2h     test.sh    632054   1   1    8gb 02:00 R 00:02
"""

def get_job_status(api_instance, args: Namespace):
    try:
        api_response = api_instance.read_namespaced_job_status(
            name=args.job_name,
            namespace=args.namespace
        )

        # Determine the state of the job
        if api_response.status.active == 1:
            job_state = "R"  # Running
        elif api_response.status.active == 0:
            job_state = "Q"  # Queued
        else:
            job_state = "C"  # Completed

        # Additional checks for various job statuses
        if api_response.status.failed:
            job_state = "F"  # Failed
        if api_response.status.succeeded:
            job_state = "S"  # Succeeded

        # R: running, C: completed, E: exiting, H: held, Q: queued, T: moved, W: waiting
        job_data = {
            "Job ID": api_response.metadata.name,
            "Username": api_response.metadata.namespace,
            "Queue": "****",
            "Jobname": "****",
            "SessID": "****",
            "NDS": "*",
            "TSK": "*",
            "Memory": "****",
            "Time": "**:**",
            "S": job_state,
            "Time2": "**:**"
        }
        job_sizes = {key: len(value) if len(value) > len(key) else len(key) for key, value in job_data.items()}
        # print(job_sizes)
        header_line = " ".join(f"{key:<{job_sizes[key]}}" for key in job_data.keys())
        print(header_line)
        print("".join(["-" * job_sizes[key] + " " for key in job_data.keys()]))
        job_line = " ".join(f"{value:<{job_sizes[key]}}" for key, value in job_data.items())
        print(job_line)
    except client.rest.ApiException as e:
        print("[FAILED] Can not get status: Status=%s : JobName=%s : Reason=%s" % (e.status, args.job_name, eval(e.body)['reason']))
        pprint(eval(e.body))
        pprint(e.headers)
        exit(1)

def parse_arguments():
    args = ArgumentParser()
    args.add_argument('--job-name', type=str, required=True, help="Cluster job id")
    args.add_argument('--namespace', type=str, required=True, help="Namespace")
    args.add_argument("--local-config", action="store_true", default=False, help="Local config")
    args.add_argument("-d", action="store_true", help="Debug mode")
    return args.parse_args()


def main():
    args = parse_arguments()

    if args.d:
        print("""Job ID Username Queue Jobname SessID NDS TSK Memory Time  S Time2
------ -------- ----- ------- ------ --- --- ------ ----- - -----
pi     ****     ****  ****    ****   *   *   ****   **:** C **:**""")
        exit(0)

    if args.local_config:
        config.load_kube_config()
    else:
        config.load_incluster_config()
    batch_v1 = client.BatchV1Api()
    get_job_status(batch_v1, args)


if __name__ == '__main__':
    main()
