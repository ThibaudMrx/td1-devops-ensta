# TD3 — Cloud Azure

**Durée :** 3h  
**Objectifs :** Déployer une application conteneurisée sur le cloud, observer le scaling automatique, mettre en place un pipeline CI/CD complet

---

## Prérequis

- Docker Desktop installé et fonctionnel
- Azure CLI installé (`az --version`)
- Un compte Azure 
- Un compte GitHub

---

## Code de départ

Pour ce TD, **forkez le repo de départ**

Il contient un code complet et fonctionnel :

```
starter-code/
├── app.py          # Application Streamlit avec try/except Redis
├── Dockerfile      # Image Streamlit prête à builder
├── requirements.txt
└── .env.example    # Template de configuration
```

**Étapes :**

1. Forkez le repo sur votre compte GitHub
2. Clonez votre fork en local
3. Copiez `.env.example` en `.env` et ajustez si besoin
4. Vérifiez que l'app tourne en local :

```bash
docker build -t enstartup:v1 .
docker run -p 8501:8501 enstartup:v1
```

Ouvrez http://localhost:8501 — vous devez voir l'interface ENStartup.

> **Note :** L'app fonctionne sans Redis (mode dégradé). Le compteur de visites sera absent, mais tout le reste est opérationnel.

---

## Exercice 1 : Azure Container Registry

### Contexte

Avant de déployer sur Azure, vous devez stocker votre image Docker quelque part. Azure Container Registry (ACR) est le registry privé d'Azure.

### Objectif

Créez un registry et poussez votre image dessus.

### Étapes

**1.1.** Connectez-vous à Azure CLI :

```bash
az login
```

**1.2.** Créez un resource group pour le TD :

```bash
az group create --name rg-enstartup --location francecentral
```

**1.3.** Créez un Azure Container Registry :

```bash
az acr create --resource-group rg-enstartup --name enstartupregistry --sku Basic
```

> Le nom doit être unique globalement et ne contenir que des lettres/chiffres.

**1.4.** Connectez Docker à votre registry :

```bash
az acr login --name enstartupregistry
```

**1.5.** Taguez votre image locale pour qu'elle pointe vers votre registry :

```bash
docker tag enstartup:v1 enstartupregistry.azurecr.io/enstartup:v1
```

**1.6.** Poussez l'image :

```bash
docker push enstartupregistry.azurecr.io/enstartup:v1
```

**1.7.** Vérifiez que l'image est bien dans le registry :

```bash
az acr repository list --name enstartupregistry
az acr repository show-tags --name enstartupregistry --repository enstartup
```

### Questions

**Q1 — Quelle est la différence entre Docker Hub et ACR ?**

> _Votre réponse :_

---

**Q2 — Pourquoi utiliser un registry privé en entreprise ?**

> _Votre réponse :_

---

### ✅ Checkpoint

- [ ] Le registry ACR est créé
- [ ] L'image est visible dans le registry

---

## Exercice 2 : Azure Container Apps 

### Contexte

Azure Container Apps est un service serverless pour exécuter des containers. Pas de VM à gérer, scaling automatique, pay-per-use.

### Objectif

Déployez votre application et obtenez une URL publique.

### Étapes

**2.1.** Créez un environnement Container Apps :

```bash
az containerapp env create \
  --name enstartup-env \
  --resource-group rg-enstartup \
  --location francecentral
```

**2.2.** Activez l'accès admin sur ACR et récupérez le mot de passe :

```bash
az acr update --name enstartupregistry --admin-enabled true
ACR_PASSWORD=$(az acr credential show --name enstartupregistry --query "passwords[0].value" -o tsv)
```

**2.3.** Déployez votre application :

```bash
az containerapp create \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --environment enstartup-env \
  --image enstartupregistry.azurecr.io/enstartup:v1 \
  --target-port 8501 \
  --ingress external \
  --registry-server enstartupregistry.azurecr.io \
  --registry-username enstartupregistry \
  --registry-password $ACR_PASSWORD \
  --cpu 0.5 \
  --memory 1.0Gi
```

**2.4.** Récupérez l'URL de votre application :

```bash
az containerapp show --name enstartup-app --resource-group rg-enstartup --query properties.configuration.ingress.fqdn -o tsv
```

**2.5.** Testez en ouvrant l'URL dans votre navigateur.

### Questions

**Q3 — Quelle est la différence entre Container Apps et une VM classique ?**

> _Votre réponse :_

---

**Q4 — Que signifie "serverless" ?**

> _Votre réponse :_

---

**Q5 — Combien de replicas tournent par défaut ?**

> _Votre réponse :_

---

### ✅ Checkpoint

- [ ] L'application est accessible via une URL publique
- [ ] Elle fonctionne comme en local

---

## Exercice 3 : Variables d'environnement 

### Contexte

Votre application utilise des variables d'environnement (`APP_TITLE`, etc.). Configurez-les dans Azure — il n'y a pas de fichier `.env` dans le cloud.

### Objectif

Passez des variables d'environnement à votre Container App.

### Étapes

**3.1.** Mettez à jour votre Container App avec des variables d'environnement :

```bash
az containerapp update \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --set-env-vars "APP_TITLE=ENStartup Production" "ENVIRONMENT=azure"
```

**3.2.** Rafraîchissez l'app et vérifiez que le titre a changé.

### Questions

**Q6 — Où sont stockées ces variables dans Azure ?**

> _Votre réponse :_

---

**Q7 — Sont-elles visibles en clair quelque part ?**

> _Votre réponse :_

---

**Q8 — En production, comment protégeriez-vous des valeurs sensibles (clés API, mots de passe) ?**

> _Votre réponse :_

---

### ✅ Checkpoint

- [ ] Le titre de l'app reflète la variable d'environnement

---

## Exercice 4 : Scaling & Load Testing 

### Contexte

L'intérêt du cloud, c'est le scaling automatique. Vous allez générer du trafic avec Locust et observer les replicas se multiplier. L'`app.py` fourni affiche déjà une couleur unique par replica — vous pourrez les distinguer visuellement.

### Objectif

Visualisez le scaling en action : observez plusieurs replicas s'allumer sous la charge.

### Étapes

**4.1.** Configurez le scaling de votre Container App :

```bash
az containerapp update \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --min-replicas 1 \
  --max-replicas 5 \
  --scale-rule-name http-scaling \
  --scale-rule-type http \
  --scale-rule-http-concurrency 10
```

**4.2.** Créez un fichier `locustfile.py` pour générer du trafic :

```python
from locust import HttpUser, task, between

class ENStartupUser(HttpUser):
    wait_time = between(0.5, 2)

    @task
    def load_homepage(self):
        self.client.get("/")
```

**4.3.** Installez et lancez Locust :

```bash
pip install locust
locust -f locustfile.py --host=https://<VOTRE-URL>
```

**4.4.** Ouvrez http://localhost:8089, configurez 50-100 utilisateurs, et lancez le test.

**4.5.** Pendant le test, rafraîchissez votre app plusieurs fois. Observez :
- La couleur dans la sidebar change-t-elle ?
- Le nom du replica change-t-il ?

**4.6.** Vérifiez le nombre de replicas dans Azure :

```bash
az containerapp replica list \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --query "[].name" -o tsv

az containerapp replica list \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --query "length(@)"
```

### Questions

**Q9 — Combien de replicas ont été créés pendant le test ?**

> _Votre réponse :_

---

**Q10 — Combien de temps faut-il pour qu'un nouveau replica démarre ?**

> _Votre réponse :_

---

**Q11 — Que se passe-t-il quand le trafic diminue ?**

> _Votre réponse :_

---

### ✅ Checkpoint

- [ ] Vous voyez différentes couleurs/replicas en rafraîchissant pendant la charge
- [ ] Le nombre de replicas augmente avec le trafic

---

## Exercice 5 : Monitoring

### Contexte

En production, il faut surveiller son application : logs, métriques, alertes.

### Objectif

Explorez les outils de monitoring Azure.

### Étapes

**5.1.** Consultez les logs de votre Container App en temps réel :

```bash
az containerapp logs show \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --follow
```

Ou les 100 dernières lignes :

```bash
az containerapp logs show \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --tail 100
```

**5.2.** Dans le portail Azure (portal.azure.com) :
- Trouvez votre Container App
- Explorez l'onglet "Metrics"
- Explorez l'onglet "Log stream"

**5.3.** Identifiez ces métriques :
- Nombre de requêtes
- Temps de réponse
- CPU/RAM utilisés
- Nombre de replicas

### Questions

**Q12 — Comment seriez-vous alerté si l'app crashe ?**

> _Votre réponse :_

---

**Q13 — Quelles métriques surveilleriez-vous en priorité ?**

> _Votre réponse :_

---

### ✅ Checkpoint

- [ ] Vous savez où trouver les logs
- [ ] Vous savez lire les métriques de base

---

## Exercice 6 : Secrets avec GitHub 

### Contexte

Les secrets (clés API, mots de passe) ne doivent jamais être dans le code. GitHub Secrets permet de les stocker de façon sécurisée et de les injecter dans la CI/CD.

### Objectif

Stockez vos credentials Azure dans GitHub Secrets et utilisez-les dans un workflow.

### Étapes

**6.1.** Créez un Service Principal Azure pour GitHub :

```bash
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

az ad sp create-for-rbac --name "github-enstartup" --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-enstartup \
  --sdk-auth
```

Copiez le JSON retourné — il ressemble à :

```json
{
  "clientId": "xxx",
  "clientSecret": "xxx",
  "subscriptionId": "xxx",
  "tenantId": "xxx"
}
```

**6.2.** Dans GitHub, allez dans Settings → Secrets and variables → Actions.

**6.3.** Créez ces secrets :
- `AZURE_CREDENTIALS` : le JSON complet du Service Principal
- `AZURE_REGISTRY` : l'URL de votre ACR (`enstartupregistry.azurecr.io`)

**6.4.** Vérifiez que les secrets sont créés (vous ne pouvez pas voir leur valeur, c'est normal).

### Questions

**Q14 — Pourquoi ne pas mettre les credentials directement dans le workflow YAML ?**

> _Votre réponse :_

---

**Q15 — Qui peut voir les secrets dans GitHub ?**

> _Votre réponse :_

---

**Q16 — Que se passe-t-il si quelqu'un fork votre repo ?**

> _Votre réponse :_

---

### ✅ Checkpoint

- [ ] Les secrets sont configurés dans GitHub
- [ ] Vous comprenez pourquoi c'est plus sécurisé que `.env`

---

## Exercice 7 : CI/CD complet

### Contexte

Automatisez le déploiement : à chaque push sur `main`, l'image Streamlit est buildée, poussée sur ACR, et l'app est redéployée automatiquement.

### Objectif

Créez un workflow GitHub Actions complet.

### Étapes

**7.1.** Créez le fichier `.github/workflows/deploy.yml` avec le contenu suivant :

```yaml
name: Build and Deploy to Azure

on:
  push:
    branches: [main]

env:
  AZURE_REGISTRY: enstartupregistry.azurecr.io
  IMAGE_NAME: enstartup
  CONTAINER_APP_NAME: enstartup-app
  RESOURCE_GROUP: rg-enstartup

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Login to ACR
        run: az acr login --name enstartupregistry
      
      - name: Build and push image
        run: |
          docker build -t ${{ env.AZURE_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .
          docker push ${{ env.AZURE_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
      
      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name ${{ env.CONTAINER_APP_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ env.AZURE_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

**7.2.** Poussez le workflow et observez l'exécution dans l'onglet Actions de GitHub.

**7.3.** Faites un changement visible dans l'app (modifiez la valeur par défaut de `APP_TITLE` dans `app.py`), poussez, et vérifiez que ça se déploie automatiquement.

### Questions

**Q17 — Combien de temps prend le déploiement complet ?**

> _Votre réponse :_

---

**Q18 — Que se passe-t-il si le build échoue ?**

> _Votre réponse :_

---

**Q19 — Comment feriez-vous pour déployer sur un environnement de staging d'abord ?**

> _Votre réponse :_

---

### ✅ Checkpoint

- [ ] Le workflow s'exécute sans erreur
- [ ] Un push sur `main` déclenche un déploiement automatique

---

## Exercice 8 : Nettoyage 

### Important !

Les ressources Azure coûtent de l'argent. Nettoyez après le TD.

```bash
az group delete --name rg-enstartup --yes --no-wait
```

Vérifiez dans le portail Azure que le resource group est bien supprimé.

---

## Bonus : Custom Domain & HTTPS 

### Objectif

Configurez un nom de domaine personnalisé avec HTTPS.

### Étapes

**B.1.** Si vous avez un domaine, configurez un CNAME vers votre URL Container Apps.

**B.2.** Ajoutez le custom domain dans Azure :

```bash
az containerapp hostname add \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --hostname <votre-domaine>

az containerapp hostname bind \
  --name enstartup-app \
  --resource-group rg-enstartup \
  --hostname <votre-domaine> \
  --environment enstartup-env \
  --validation-method CNAME
```

**B.3.** Azure génère automatiquement un certificat HTTPS via Let's Encrypt.

### Alternative sans domaine

Explorez les options de certificat managé dans le portail Azure.

---

## Bonus : Comparaison de coûts

### Objectif

Estimez le coût de votre déploiement.

### Étapes

**B.4.** Utilisez le [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)

**B.5.** Estimez le coût mensuel pour :
- Container Apps avec 1 replica en moyenne
- Container Apps avec 3 replicas en moyenne
- Équivalent sur AWS (ECS Fargate) ou GCP (Cloud Run)

### Questions

**Q20 — Quel serait le coût pour 1000 utilisateurs/jour ?**

> _Votre réponse :_

---

**Q21 — À partir de quand une VM serait-elle plus rentable ?**

> _Votre réponse :_



## Ressources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure CLI Reference](https://learn.microsoft.com/cli/azure/)
- [GitHub Actions for Azure](https://github.com/Azure/actions)
- [Locust Documentation](https://locust.io/)
