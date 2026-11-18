## Résumé

Site web d'Orange County Lettings

## Architecture

- `oc_lettings_site` : configuration Django, URL principales et page d'accueil.
- `lettings` : modèles `Address` et `Letting`, vues, URL, administration et templates des locations.
- `profiles` : modèle `Profile`, vues, URL, administration et templates des profils.
- `templates/base.html` : template commun aux trois applications.

Les URL publiques restent identiques. Les noms des URL des applications sont
`lettings:index`, `lettings:letting`, `profiles:index` et `profiles:profile`.

## Développement local

### Prérequis

- Compte GitHub avec accès en lecture à ce repository
- Git CLI
- SQLite3 CLI
- Interpréteur Python 3.8 pour les versions historiques des dépendances de ce projet

Les versions de `pytest` et `six` sont fixées dans `requirements.txt` pour permettre
l'utilisation de `pytest-django==3.9.0`.

Dans le reste de la documentation sur le développement local, il est supposé que la commande `python` de votre OS shell exécute l'interpréteur Python ci-dessus (à moins qu'un environnement virtuel ne soit activé).

### macOS / Linux

#### Cloner le repository

- `cd /path/to/put/project/in`
- `git clone https://github.com/OpenClassrooms-Student-Center/Python-OC-Lettings-FR.git`

#### Créer l'environnement virtuel

- `cd /path/to/Python-OC-Lettings-FR`
- `python -m venv venv`
- `apt-get install python3-venv` (Si l'étape précédente comporte des erreurs avec un paquet non trouvé sur Ubuntu)
- Activer l'environnement `source venv/bin/activate`
- Confirmer que la commande `python` exécute l'interpréteur Python dans l'environnement virtuel
`which python`
- Confirmer que la version de l'interpréteur Python est la version 3.8 `python --version`
- Confirmer que la commande `pip` exécute l'exécutable pip dans l'environnement virtuel, `which pip`
- Pour désactiver l'environnement, `deactivate`

#### Exécuter le site

- `cd /path/to/Python-OC-Lettings-FR`
- `source venv/bin/activate`
- `pip install --requirement requirements.txt`
- Sauvegarder le fichier `oc-lettings-site.sqlite3` avant la première migration.
- `python manage.py migrate`
- `python manage.py runserver`
- Aller sur `http://localhost:8000` dans un navigateur.
- Confirmer que le site fonctionne et qu'il est possible de naviguer (vous devriez voir plusieurs profils et locations).

Les migrations créent les nouvelles tables, copient les données existantes avec
l'ORM Django (en conservant les identifiants et les relations), puis suppriment
les anciennes tables. Il ne faut pas supprimer la base ni l'ancienne migration
`oc_lettings_site/migrations/0001_initial.py`.

#### Linting

- `cd /path/to/Python-OC-Lettings-FR`
- `source venv/bin/activate`
- `flake8`

#### Tests unitaires

- `cd /path/to/Python-OC-Lettings-FR`
- `source venv/bin/activate`
- `pytest`

Les tests sont regroupés dans le fichier `tests.py` de chaque application. Ils
vérifient les vues, les URL, les modèles, l'administration, les pages d'erreur et
la migration des données existantes.

#### Couverture des tests

Après l'installation des dépendances et l'activation de l'environnement virtuel :

```console
python -m coverage run -m pytest
python -m coverage report -m
python -m coverage html
```

Le rapport HTML est disponible dans `htmlcov/index.html`. La configuration
`.coveragerc` mesure les lignes et les branches de l'ensemble du projet, y compris
les migrations et les fichiers de démarrage. Les fichiers `tests.py` et
l'environnement `venv` sont exclus de cette mesure.

La commande `coverage report` échoue si la couverture est inférieure à 81 %, afin
de garantir une couverture supérieure à 80 %. Les rapports générés sont ignorés
par Git.

#### Pages d'erreur

Les templates partagés `templates/404.html` et `templates/500.html` personnalisent
les réponses d'erreur standard de Django lorsque `DEBUG=False`. Une location ou
un profil introuvable renvoie une erreur 404. Une erreur inattendue renvoie une
page 500 sans afficher les détails techniques de l'exception.

La configuration locale conserve `DEBUG=True` pour le développement. Les tests
des pages d'erreur utilisent temporairement `DEBUG=False`, sans changer ce réglage.

#### Base de données

- `cd /path/to/Python-OC-Lettings-FR`
- Ouvrir une session shell `sqlite3`
- Se connecter à la base de données `.open oc-lettings-site.sqlite3`
- Afficher les tables dans la base de données `.tables`
- Afficher les colonnes dans le tableau des profils, `pragma table_info(profiles_profile);`
- Lancer une requête sur la table des profils, `select user_id, favorite_city from
  profiles_profile where favorite_city like 'B%';`
- `.quit` pour quitter

#### Panel d'administration

- Aller sur `http://localhost:8000/admin`
- Connectez-vous avec l'utilisateur `admin`, mot de passe `Abc1234!`

### Windows

Utilisation de PowerShell, comme ci-dessus sauf :

- Pour activer l'environnement virtuel, `.\venv\Scripts\Activate.ps1` 
- Remplacer `which <my-command>` par `(Get-Command <my-command>).Path`
