# Install Prometheus and Graphana

Kube Prometheus Stack – powerful monitoring stack
Above we focused on how Helm Charts works and how to deploy the simplest monitoring, here we will try to do a quick overview of more advanced and complex set up.

Kube Prometheus Stack is a repository, which collects Kubernetes manifests, Grafana dashboards, and Prometheus rules combined with documentation and scripts. This provides easy to operate end-to-end Kubernetes cluster monitoring with Prometheus using the Prometheus Operator.

We install it similarly like earlier, but we provide a kube-prometheus-stack repository.

```shell

# Create Namespaces monitoring and observability
kubectl create namespace monitoring
kubectl create namespace observability

# Add repo to helm 
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update



# Install Prometheus Stack
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --kubeconfig /etc/rancher/k3s/k3s.yaml

# Expose Service Grafana
kubectl patch svc "prometheus-grafana" -n "monitoring" -p '{"spec":{"type":"LoadBalancer"}}'

# Expose Service Proteus
kubectl patch svc "prometheus-operated" -n "monitoring" -p '{"spec":{"type":"ClusterIP"}}'

kubectl --namespace monitoring port-forward svc/prometheus-grafana --address 0.0.0.0 3000:80 &
kubectl --namespace monitoring port-forward svc/prometheus-operated --address 0.0.0.0 9090 &
```

# Install Jaeger

```shell
# Create namespace
kubectl create namespace observability

## Please use the last stable version
export jaeger_version=v1.28.0 
## jaegertracing.io_jaegers_crd.yaml
kubectl create -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/${jaeger_version}/deploy/crds/jaegertracing.io_jaegers_crd.yaml
## service_account.yaml
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/${jaeger_version}/deploy/service_account.yaml
## role.yaml
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/${jaeger_version}/deploy/role.yaml
## role_binding.yaml
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/${jaeger_version}/deploy/role_binding.yaml
## operator.yaml
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/${jaeger_version}/deploy/operator.yaml

########
# Expand the roles to the Cluster. In other words, enable the cluster-wide permissions:
########

## cluster_role.yaml
kubectl create -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/${jaeger_version}/deploy/cluster_role.yaml
## cluster_role_binding.yaml
kubectl create -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/${jaeger_version}/deploy/cluster_role_binding.yaml

# Should return ‘jaeger-operator’
kubectl get deployment  -n observability

###
# Create Ingress Service
###
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.0.3/deploy/static/provider/cloud/deploy.yaml

# Create a Jaeger instance
kubectl apply -n observability -f - <<EOF
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: simplest
EOF

# Port Forwarding
kubectl port-forward -n observability  service/simplest-query --address 0.0.0.0 16686:16686

```

## Tagging Application

```python
import logging
from jaeger_client import Config
from opentracing.ext import tags
from opentracing.propagation import Format
import requests

def init_tracer(service):
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
        },
        service_name=service,
    )
    # this call also sets opentracing.tracer
    return config.initialize_tracer()

tracer = init_tracer('first-service')

def test():
    # Add your test function here
    with tracer.start_span('my-test-span') as span:
        req =requests.get('https://udacity.com')
        span.set_tag('http.methods', req)
        def format():
            with tracer.start_span('my-test-span') as span:
                try:
                    print("success!")
                except:
                    print("try again")
    
if __name__ == "__main__":
    test()
    
    tracer.close()
```

## Creating a Jaeger Example App
```shell
# Create Application
kubectl apply -n observability -f - <<EOF
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
    name: hotrod
EOF

# Check if Running
kubectl get svc -l app.kubernetes.io/instance=hotrod  -n observability

# Deploy hotrod app
kubectl apply -f  hotrod.yaml

##################
# Port Forwarding
##################
# Port forward the service/hotrod-query
kubectl port-forward -n observability  service/hotrod-query --address 0.0.0.0 16686:16686

```

# Create Dashboards

## Protheus Monitoring

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    name: app
  name: {frontend-app, backend-app}
  namespace: default
spec:
  endpoints:
  - interval: 30s
    targetPort: 8080
    path: /metrics
  selector:
    matchLabels:
      app: {frontend-app, backend-app}
```
