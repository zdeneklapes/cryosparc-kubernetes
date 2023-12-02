# Cryosparc-kubernetes

This is a collection of scripts and configuration files to deploy cryosparc on kubernetes.

# Installation
Entrypoints and templates are located in the `entrypoints` directory.

## Apply
```bash
kubectl apply -f deploy/kubernetes
kubectl apply -f deploy/kubernetes/pvc
```

When all configuration files are applied, the application can be accessed on [cryosparc.dyn.cloud.e-infra.cz](cryosparc.dyn.cloud.e-infra.cz).

The default username/email is `a@a.com` and the default password is `a`.

## Delete
```bash
./make.sh clean_kubernetes
```

# Usage:

## Create a new image

The IP for `ssh` command must be changed (for you) inside the called functions _(It is setup for me right now)_

```bash
./make.sh pack send build_push_cryosparc_on_remote
```

# Other resources

[//]: # (URL)

- [Cryosparc-Docs](https://cryosparc.com/docs/)
- [Multi-Container Pods in Kubernetes](https://linchpiner.github.io/k8s-multi-container-pods.html#:~:text=A%20Pod%20is%20is%20the,containers%20are%20relatively%20tightly%20coupled.)
