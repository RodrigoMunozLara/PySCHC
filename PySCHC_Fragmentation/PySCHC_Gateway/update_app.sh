#!/bin/bash
PROJECT_ID=pyschc-project-273514
COMPUTE_ENGINE_ZONE=us-west1-a
APP_NAME=pyschc-app:v48
SERVICE_NAME=pyschc-app-kubernetes
CLUSTER_NAME=pyschc-cluster

gcloud config set project ${PROJECT_ID}
gcloud config set compute/zone ${COMPUTE_ENGINE_ZONE}
gcloud auth configure-docker

echo ""
echo "Borrando las imagenes y containers anteriores de docker......."
#sudo docker image rm $(sudo docker image ls -q)
sudo docker container prune

echo ""
echo "Construyendo imagen para subir a Google Cloud Repository......"
sudo docker build -t gcr.io/${PROJECT_ID}/${APP_NAME} .

echo ""
echo "Enviando imagen a Google Cloud Repository....................."
gcloud auth configure-docker
sudo docker push gcr.io/${PROJECT_ID}/${APP_NAME}

echo ""
echo "Fetching cluster endpoint and auth data......................."
sudo gcloud container clusters get-credentials ${CLUSTER_NAME}

echo ""
echo "Instalando imagen en Google Kubernetes Engine................."
sudo kubectl create deployment ${SERVICE_NAME} --image=gcr.io/${PROJECT_ID}/${APP_NAME}

echo ""
echo "Exponiendo aplicacion a Internet.............................."
sudo kubectl expose deployment ${SERVICE_NAME} --type=LoadBalancer --port 8080 --target-port 8080

echo ""
echo "Obteniendo la lista de pods..................................."
sudo kubectl get pods

echo ""
echo "Obteniendo la lista de servicios.............................."
sudo kubectl get services
