# mongodb

# Prerequisites:
- `Kubernetes Cluster`: Ensure you have access to a Kubernetes cluster (local or remote).
- `Helm Installed`: Install Helm on your system.
- `kubectl Installed`: Use kubectl to interact with the cluster.

# Steps to Deploy the Helm Chart:

1. Create a Namespace (optional):

```
kubectl create namespace mongodb
```

2. Install the Chart: Navigate to the directory containing the Chart.yaml file and run:
```
helm install mongodb-release . -n mongodb
```

Replace mongodb-release with the desired release name.

3. Check the Resources: Verify that all the resources have been created successfully:
```
kubectl get all -n mongodb
```
4. Expose the MongoDB Service Locally: Since there's no ingress, you can use port-forwarding to access MongoDB locally:
```
kubectl port-forward svc/mongodb-release-mongodb 27017:27017 -n mongodb
```
This will forward the MongoDB service to your local machine on port 27017.
MongoDB will be accessible locally at localhost:27017.

# Accessing MongoDB:

- Use the MongoDB CLI (mongo) or any MongoDB client to connect:

```
mongo --host localhost --port 27017 -u admin -p secure-password --authenticationDatabase admin
```
Replace admin and secure-password with the credentials defined in your values.yaml.

# Notes:

### 1. No Ingress:
- Without ingress, MongoDB cannot be accessed externally.
- This is generally fine for internal databases or when connecting only from within the cluster.

### 2. Storage
- Persistent volumes will retain data even if the pod is restarted.
- Verify your cluster supports the storageClass defined in templates/storageclass.yaml.

### 3. Configurations
- MongoDB is configured securely using ConfigMap and Secret.
- Default replication is set to 3 replicas for production use.
