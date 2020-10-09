# Fluent-bit Storage Metrics Exporter 

Prometheus exporter for storage metrics about fluent-bit, written in Python Flask.
Storage metrics are supported from fluent-bit version 1.5.0 and above.

### Installation
Before actually using it, test it thoroughly with docker-compose on your localhost.

#### Docker

```bash
$ docker pull danielkim/fluent-bit-storage-exporter:1.0.0
$ docker run --rm -p 8080:8080 danielkim/fluent-bit-storage-exporter:1.0.0
$ curl localhost:8080/parse/${FLUENT_BIT_HOST_WITH_PORT}
```

Easily run exporter using docker-compose.
```bash
$ cd ./example/docker-compose
$ docker-compose up
...
Starting example_fluent_bit_1                  ... done
Starting example_fluent_bit_storage_exporter_1 ... done
...
$ curl localhost:8080/parse/fluent_bit:2020
# TYPE fluentbit_storage_layer_chunks_total_chunks gauge
...
```

#### Kubernetes
You can find the `deployment.yaml` and `service.yaml` file that you can apply right away in the example directory.
Use after modifying the yaml file according to the cluster state.
```bash
$ kubectl apply -f ./example/kubernetes
```

### Collect Metrics

You can collect storage metrics by adding a job from prometheus installed in Kubernetes.
```
- job_name: 'kubernetes-fluent-bit-storage'
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_scrape]
    action: keep
    regex: true
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_port]
    action: keep
    regex: (\d+)
  - source_labels: [__meta_kubernetes_pod_ip, __meta_kubernetes_pod_annotation_prometheus_port]
    action: replace
    regex: (.+);(.+)
    replacement: /parse/$1:$2
    target_label: __metrics_path__
  - target_label: __address__
    replacement: fluent-bit-storage-exporter:80
  - source_labels: [__meta_kubernetes_pod_container_name]
    action: keep
    regex: fluent-bit.*
  - action: labelmap
    regex: __meta_kubernetes_pod_label_(.+)
  - source_labels: [__meta_kubernetes_namespace]
    action: replace
    target_label: namespace
  - source_labels: [__meta_kubernetes_pod_name]
    action: replace
    target_label: pod_name
```

## Credit & License

`fluent_bit_storage_expoter` is maintained by danielzepp
and licensed under the terms of the Apache license.
