# Annuaire Partagé (Client/Serveur)

Une application Python simulant une architecture Client/Serveur pour la gestion d'annuaires téléphoniques partagés. Ce projet utilise des échanges de fichiers JSON pour simuler la communication réseau et des fichiers CSV pour le stockage des données.

## Fonctionnalités

### Utilisateur Standard
* **Connexion sécurisée** (Mots de passe hachés en SHA-512).
* **Gestion de contacts (CRUD)** : Ajouter, Modifier, Supprimer des contacts dans son propre annuaire.
* **Recherche** : Rechercher des contacts par mots-clés.
* **Système de Permissions** : Accorder ou retirer le droit à d'autres utilisateurs de consulter votre annuaire.
* **Consultation** : Voir les annuaires des utilisateurs qui vous ont donné la permission.

### Administrateur
* **Gestion des Comptes** : Créer, Modifier (Reset MDP/Rôle), Supprimer des comptes utilisateurs.
* **Statistiques** : Vue d'ensemble du serveur (nombre d'annuaires, nombre de contacts, etc.).

### Serveur
* **Logs en temps réel** : Affichage des actions (Connexion, Requêtes, Erreurs) dans la console serveur.
* **Persistance des données** : Stockage automatique dans des fichiers CSV.

---

## Prérequis

* **Python 3.x** installé sur votre machine.
* Aucune bibliothèque externe n'est requise (utilise uniquement la bibliothèque standard : `os`, `csv`, `json`, `time`, `pathlib`, `hashlib`, etc.).

---

## Structure du Projet

```text
/racine_du_projet
│
├── main.py               # Script de lancement automatique (Client + Serveur)
├── code/
│   ├── serveur.py            # Le programme Serveur
│   ├── client.py             # Le programme Client (Interface Utilisateur)
│   ├── mes_fonctions.py      # Fonctions utilitaires (Affichage, Saisie)
│   └── connexion_ClientServeur.py  # Module réseau (Gestion PDU JSON)
│
└── donnee_serveur/           # (Généré automatiquement au lancement)
    ├── comptes.csv           # Base de données des utilisateurs
    ├── permissions.csv       # Matrice des droits d'accès
    ├── pdu_requete.json      # Fichier tampon pour les demandes
    ├── pdu_reponse.json      # Fichier tampon pour les réponses
    └── annuaires/            # Dossier contenant les annuaires CSV individuels
```

---

## Installation et Lancement

1. **Cloner ou télécharger** le dossier du projet.
2. Ouvrir un terminal dans la racine du projet.

**Option 1 : Lancement Automatique (Recommandé)**

Ce script détecte votre OS (Windows, Linux, macOS) et ouvre deux fenêtres de terminal séparées : une pour le serveur, une pour le client.

```bash
python main.py
```

**Option 2 : Lancement Manuel**

Si le launcher ne fonctionne pas, ouvrez deux terminaux distincts.

**Terminal 1 (Serveur) :**

```bash
cd code
python serveur.py
```

*Attendez que le message "SERVEUR EN LIGNE" apparaisse.*

**Terminal 2 (Client) :**

```bash
cd code
python client.py
```

---

## Première Connexion (Compte Admin par défaut)

Au premier lancement, le serveur détecte l'absence de comptes et crée automatiquement un administrateur par défaut :

- **Utilisateur :** `aoun`
- **Mot de passe :** `stri26`

*Une fois connecté, vous pouvez créer d'autres comptes utilisateurs via le menu Administration.*

---

## Fonctionnement Technique

L'application simule un réseau via le système de fichiers :

1. **Requête (Client -> Serveur) :** Le client génère un dictionnaire Python (Action, Demandeur, Corps), le convertit en JSON et l'écrit dans `pdu_requete.json`.
2. **Traitement (Serveur) :** Le serveur surveille la présence de ce fichier. Dès qu'il apparaît, il le lit, traite la demande (vérification des droits, modification des CSV) et supprime le fichier de requête.
3. **Réponse (Serveur -> Client) :** Le serveur écrit le résultat (Status, Message, Donnée) dans `pdu_reponse.json`.
4. **Réception (Client) :** Le client, qui attendait, lit la réponse, l'affiche à l'utilisateur et supprime le fichier de réponse.

**Codes de Statut (Status Codes)**
- `200` : Succès
- `201` : Création réussie
- `400` : Mauvaise requête / Champs manquants
- `401` : Non Autorisé / Mauvais mot de passe
- `403` : Interdit (Permission refusée pour voir un annuaire)
- `404` : Non trouvé (Contact ou Compte inexistant)
- `409` : Conflit (Le compte/contact existe déjà)
- `50x` : Erreurs serveur / Timeout

---

## Notes Importantes

- **Sécurité des fichiers :** Ne supprimez pas manuellement les fichiers `.json` pendant l'exécution, cela pourrait bloquer la communication.
- **Réinitialisation :** Pour remettre le serveur à zéro, utilisez l'option "2. Réinitialiser les données" dans le menu du Serveur, ou supprimez manuellement le dossier `donnee_serveur`.

---

## Auteurs

Projet réalisé dans le cadre d'un exercice d'architecture simulation réseau entre Client/Serveur en Python.

Par : **Abasse ALI** et **Ayyub BOUTAHIR**