# Cryosparc-kubernetes

This is a collection of scripts and configuration files to deploy cryosparc on kubernetes.

# Installation
Entrypoints and templates are located in the `entrypoints` directory.

## Apply
```bash
kubectl apply -f deploy/kubernetes
kubectl apply -f deploy/kubernetes/pvc
```

## Delete
```bash
./make.sh clean_kubernetes
```


# Usage:

## Create a new image

```bash
./make.sh pack send build_push_cryosparc_on_remote
```

# Other resources

[//]: # (URL)

- [Cryosparc-Docs](https://cryosparc.com/docs/)
- [Multi-Container Pods in Kubernetes](https://linchpiner.github.io/k8s-multi-container-pods.html#:~:text=A%20Pod%20is%20is%20the,containers%20are%20relatively%20tightly%20coupled.)