# Python Microservices EKS MP4 to MP3 Converter

## Overview

This project provides a microservices-based solution for converting MP4 video files to MP3 audio files. The architecture ensures scalability, fault tolerance, and easy deployment using Docker Compose or Helm charts. The solution leverages key components such as API Gateway, MongoDB, RabbitMQ, and individual microservices for authentication, conversion, notifications, and API Gateway routing.

---

## Features

- **create user**: Creates a new user with the provided credentials.

- **login and generate JWT token**: Authenticates a user and generates a JWT token for subsequent API calls.

- **Video Upload and Initial Request Handling**  
  - Users upload videos to be converted into MP3 files.
  - The API Gateway handles incoming requests and coordinates the process.

- **Storing Video and Queuing for Processing**  
  - Uploaded videos are stored in MongoDB.
  - A message is placed on RabbitMQ to notify downstream services about new videos.

- **Video to MP3 Conversion**  
  - A dedicated microservice processes the queue messages.
  - Converts MP4 videos to MP3 and stores the results in MongoDB.
  - Sends a notification message to inform clients of completion.

- **Notification Service**  
  - Sends an email to clients notifying them that the MP3 file is ready for download.

- **Client Download Request**  
  - Clients download the MP3 file using a unique ID and JWT for authentication.

---

## Architecture

![Project Architecture](./project-architecture/ProjectArchitecture.png)

---

## Prerequisites

1. **Docker** and **Docker Compose** installed on your system to test locally.
2. **Install Helm** Helm is a Kubernetes package manager.
3. **Python 3.10+** for development and running individual services locally.
4. **Create an AWS Account** If you do not have an AWS account.
5. **AWS CLI** Install the AWS Command Line Interface (CLI) following the official installation guide.
6. **Install kubectl** Install the latest stable version of kubectl on your system.
7. **Databases** Set up PostgreSQL and MongoDB for your application.

---

## Setup and Deployment

### Using Docker Compose

1. Clone the repository:
   ```
   git clone https://github.com/rahulkataria35/python_microservices_eks_mp4_to_mp3.git
   cd python_microservices_eks_mp4_to_mp3
   ```

2. Navigate to the Docker deployment folder:
```
cd dockerised_deployment
```
3. Start the services:
```
docker-compose up --build
```

# Import the Postman Collection and test the APIs
1. Import the Postman Collection from the `postman_collection` folder.
2. Run the APIs using the Postman Collection.
3. Verify the APIs are working as expected.
4. Test the APIs with different inputs and edge cases.


### High Level Flow of Application Deployment Using Helm Charts (Kubernetes Deployment)

1. Ensure your Kubernetes cluster is configured.

2. Navigate to the Helm charts directory:
```
cd helm_charts
```
3. Install MongoDB, RabbitMQ, and PostgreSQL:
```
helm install mongo-db ./mongo-db
helm install rabbitmq ./rabbitmq
helm install postgresql ./postgresql
```

4. Deploy Microservices:

- auth-server: Navigate to the auth-server manifest folder and apply the configuration.
- gateway-server: Deploy the gateway-server.
- converter-module: Deploy the converter-module. Make sure to provide your email and password in converter/manifest/secret.yaml.
- notification-server: Configure email for notifications and two-factor authentication (2FA).

5. Application Validation: Verify the status of all components by running:
```
kubectl get all
```
6. Destroying the Infrastructure


### Low Level Steps

**Cluster Creation**
1. Log in to AWS Console:
    - Access the AWS Management Console with your AWS account credentials.

2. Create eksCluster IAM Role:
    - Navigate to the IAM dashboard and create a new role with the necessary permissions.
    - Follow the steps using root user (url: https://docs.aws.amazon.com/eks/latest/userguide/cluster-iam-role.html)
    - Attach the **AmazonEKSClusterPolicy** and **AmazonEKSServiceRolePolicy** to the role.
    - Create a new cluster with the role and configure the cluster settings.

3. Create Node Role - AmazonEKSNodeRole
    - Create a new role with the necessary permissions. (url: https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html#create-worker-node-role)
    - Please note that you do NOT need to configure any VPC CNI policy mentioned after step 5.e under Creating the Amazon EKS node IAM role.
    - Simply attach the following policies to your role once you have created **AmazonEKS_CNI_Policy** , **AmazonEBSCSIDriverPolicy** , **AmazonEC2ContainerRegistryReadOnly**, **AmazonEKSWorkerNodePolicy** incase it is not attached by default.
    - Create a new node group with the role and configure the node settings.
    - Your AmazonEKSNodeRole will look like this:

5. Open EKS Dashboard:
    - Navigate to the Amazon EKS service from the AWS Console dashboard.

6. Create EKS Cluster:
    - Click on the "Create cluster" button.
    - Choose the IAM role you created in step 2.
    - Choose the VPC and subnets you want to use.
    - Choose the instance type for your worker nodes.
    - Click on "Create cluster" button.
    - Wait for the cluster to provision, which may take several minutes.
    - Once the cluster status shows as "Active," you can now create node groups.

7. Node Group Creation:
    - In the "Compute" section, click on "Add node group."
    - Choose the instance type for your worker nodes.
    - Choose the number of nodes you want to create.
    - Click on "Create node group" button.

8. Adding inbound rules in Security Group of Nodes

- NOTE: Ensure that all the necessary ports are open in the node security group.

9. Enable EBS CSI Addon:
    - enable addon **ebs csi** this is for enabling pvcs once cluster is created.
    
10. Deploying your application on EKS Cluster
    - Clone the code from this repository.
    - Set the cluster context
    ```
    aws eks update-kubeconfig --name <cluster_name> --region <aws_region>
    ```

# Commands

Here are some essential Kubernetes commands for managing your deployment:

1. **MongoDB**
Navigate to the Helm charts directory:
```
cd helm_charts
```
To install MongoDB, set the database username and password in values.yaml, then navigate to the MongoDB Helm chart folder and run:

Install MongoDB

```
helm install mongo-db ./mongo-db
```
- Connect to the MongoDB instance using:

```
mongosh mongodb://<username>:<pwd>@<nodeip>:30005/mp3s?authSource=admin
```

2. **PostgreSQL**
Set the database username and password in values.yaml. Install PostgreSQL from the PostgreSQL Helm chart folder.

```
cd ../Postgres
helm install postgres .
```

3. **RabbitMQ**
Deploy RabbitMQ by running:

```
cd ../rabbitmq
helm install rabbitmq .
```


### Apply the manifest file for each microservice:

- Auth Service:
    ```
    cd src/auth/manifests
    kubectl apply -f .    
    ```
- Gateway Service (Producer):
    ```
    cd src/gateway/manifests
    kubectl apply -f .
    ```
- Converter Service (Consumer):
    ```
    cd src/converter/manifests
    kubectl apply -f .
    ```
- Notification Service (Consumer):
    ```
    cd src/notification/manifests
    kubectl apply -f .
    ```

### Application Validation
After deploying the microservices, verify the status of all components by running:
```
kubectl get all
```
### Notification Configuration
- For configuring email notifications and two-factor authentication (2FA), follow these steps:

- Go to your Gmail account and click on your profile.

- Click on "Manage Your Google Account."

- Navigate to the "Security" tab on the left side panel.

- Enable "2-Step Verification."

- Search for the application-specific passwords. You will find it in the settings.

- Click on "Other" and provide your name.

- Click on "Generate" and copy the generated password.

- Paste this generated password in notification-service/manifest/secret.yaml along with your email.

Run the application through the following API calls:

### API Definition

- user create endpoint 
    ```
    POST http://nodeIP:30002/create
    ```
- login endpoint:
    ```
    POST http://nodeIP:30002/login
    ```
- upload endpoint:
    ```
    POST http://nodeIP:30002/upload
    ```
- download endpoint:
    ```
    GET http://nodeIP:30002/download
    ```

### Destroying the Infrastructure
To clean up the infrastructure, follow these steps:
    - Delete the Node Group: Delete the node group associated with your EKS cluster.

    - Delete the EKS Cluster: Once the nodes are deleted, you can proceed to delete the EKS cluster itself.







