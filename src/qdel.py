#!/usr/bin/python3
from pprint import pprint

from kubernetes import client, config
from argparse import ArgumentParser, Namespace

def delete_job(api_instance, args: Namespace):
    try:
        api_response = api_instance.delete_namespaced_job(
            name=args.job_name,
            namespace=args.namespace,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )
        print("[DELETED] JobName=%s" % args.job_name)
    except client.rest.ApiException as e:
        print("[FAILED] Can not delete: Status=%s : JobName=%s : Reason=%s" % (e.status, args.job_name, eval(e.body)['reason']))
        pprint(eval(e.body))
        pprint(e.headers)
        exit(1)


def parse_arguments():
    args = ArgumentParser()
    args.add_argument("--job-name", type=str, required=True, help="Name of the job")
    args.add_argument('--namespace', type=str, required=True, help="Namespace")
    args.add_argument("--local-config", action="store_true", default=False, help="Local config")
    args.add_argument('-d', action="store_true", help="Debug mode")
    return args.parse_args()


def main():
    args = parse_arguments()

    if args.d:
        print("[DELETED] JobName=pi")
        exit(0)

    if args.local_config:
        config.load_kube_config()
    else:
        config.load_incluster_config()
    batch_v1 = client.BatchV1Api()
    delete_job(batch_v1, args)


if __name__ == '__main__':
    main()
