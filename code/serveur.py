"""
Serveur
"""

import os
import csv
import time
import json
import shutil
import mes_fonctions
from pathlib import Path
from datetime import datetime
import connexion_ClientServeur as reseau

DOSSIER_DATA = Path("donnee_serveur")
FICHIER_COMPTES = DOSSIER_DATA / "comptes.csv"
FICHIER_PERMISSIONS = DOSSIER_DATA / "permissions.csv"
DOSSIER_ANNUAIRES = DOSSIER_DATA / "annuaires"

"""
Présentation des "status" :
    Succès :
        - 200 (Succès) : Connexion réussie, contact ajouté, liste de contacts récupérée.
        - 201 (Créé) : Uniquement lors de la Création de Compte.
        
    Erreur :
        - 400 (Mauvaise Requête) : L'utilisateur a oublié de taper le Nom ou le Prénom d'un contact, ou l'action demandée n'existe pas.
        - 401 (Non Autorisé) : Mauvais mot de passe lors du login, ou tentative d'ajout de contact sans être connecté.
        - 403 (Interdit) : C'est le code des Permissions. Si un utilisateur essaie de voir l'annuaire d'un autre mais que celui ci ne lui a pas donné la permission, le serveur renvoie 403.
        - 404 (Non Trouvé) : Utilisé si on cherche l'annuaire d'un utilisateur qui n'existe pas (le fichier .csv est introuvable).
        - 409 (Conflit) : Utilisé lors de la création de compte si le nom d'utilisateur existe déjà. On ne peut pas écraser un compte existant.
        - 500 (Erreur Interne) : Le fichier de réponse JSON est vide, illisible, ou le client n'est pas connecté via connecter_serveur().

Client -> Serveur (Requete) :
    PDU :
        {
            "action": "NOM_DE_L_ACTION",
            "demandeur": "Nom_Utilisateur_Connecté",
            "corps":{
                "parametre_1": "valeur",
                "parametre_2": "valeur"
            }
        }
        
Serveur -> Client (Reponse) :
    PDU :
        {
            "status": code_status,
            "message": "Texte explicatif pour l'humain",
            "donnee": [ ... ]
        }
"""

def Creation_Compte(donnee):
    """
    Crée un nouvel utilisateur dans le fichier CSV des comptes et initialise son fichier annuaire.
    
    Args:
        donnee (dict): Contient 'nom', 'mot_de_passe' et 'statut'.
        
    Returns:
        dict: Réponse PDU avec status 201 (Succès) ou 409 (Compte existant).
    """
    nom = donnee.get("nom")
    mdp = donnee.get("mot_de_passe")
    statut = donnee.get("statut")
    annuaire = DOSSIER_ANNUAIRES / f"annuaire_{nom}.csv"

    if FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "r", encoding="utf-8") as fichier:
            for ligne in csv.DictReader(fichier):
                if ligne["Nom"] == nom:
                    return {"status": 409, "message": f"Le compte '{nom}' existe déjà"}

    with open(FICHIER_COMPTES, "a", newline="", encoding="utf-8") as fichier:
        csv.writer(fichier).writerow([nom, statut, mdp])

    with open(annuaire, "w", encoding="utf-8") as fichier:
        fichier.write("Nom,Prenom,Telephone,Adresse,Email\n")
        
    return {"status": 201, "message": "Compte créé avec succès"}

def Ajout_Contact(donnee, demandeur):
    """
    Ajoute un nouveau contact dans l'annuaire CSV de l'utilisateur demandeur.
    Vérifie les champs obligatoires et l'existence préalable du contact.
    
    Args:
        donnee (dict): Contient les infos du contact ('Nom', 'Prenom', etc.).
        demandeur (str): Nom de l'utilisateur connecté.
        
    Returns:
        dict: Réponse PDU avec status 200 (Succès), 400 (Champs manquants) ou 409 (Existe déjà).
    """
    # Validation des données entrantes (Sécurité basique)
    contact = donnee.get("contact")
    if not (contact.get("Nom") and contact.get("Prenom") and contact.get("Email")):
        return {"status": 400, "message": "Nom/Prénom/Email requis"}

    path = DOSSIER_ANNUAIRES / f"annuaire_{demandeur}.csv"
    # Vérification d'existence du fichier annuaire
    if not path.exists(): return {"status": 404, "message": "Annuaire introuvable"}

    lignes = []
    # Vérification de doublon : On doit lire le fichier avant d'écrire
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        lignes = list(reader)
        for ligne in lignes:
            if ligne["Nom"] == contact["Nom"] and ligne["Prenom"] == contact["Prenom"]:
                 return {"status": 409, "message": "Ce contact existe déjà"}
    
    # ÉCRITURE : Mode "a" (Append). On ajoute juste une ligne à la fin.
    with open(path, "a", newline="", encoding="utf-8") as fichier:
        w = csv.DictWriter(fichier, fieldnames=["Nom", "Prenom", "Telephone", "Adresse", "Email"])
        w.writerow(contact)
    return {"status": 200, "message": "Contact ajouté"}

def Recherche_Contact(donnee, demandeur):
    """
    Effectue une recherche par mot-clé dans l'annuaire d'un utilisateur cible.
    Vérifie d'abord si le demandeur a le droit d'accès.
    
    Args:
        donnee (dict): Contient 'proprietaire_cible' et 'recherche' (le terme).
        demandeur (str): Nom de l'utilisateur qui effectue la recherche.
        
    Returns:
        dict: Liste des contacts correspondants ou code d'erreur (403).
    """
    cible = donnee.get("proprietaire_cible")
    terme = donnee.get("recherche", "").lower()

    if not Verification_Droit(demandeur, cible):
        return {"status": 403, "message": "Accès refusé"}

    path = DOSSIER_ANNUAIRES / f"annuaire_{cible}.csv"
    resultats = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as fichier:
            for ligne in csv.DictReader(fichier):
                if terme in ligne["Nom"].lower() or terme in ligne["Prenom"].lower() or terme in ligne["Telephone"].lower() or terme in ligne["Adresse"].lower() or terme in ligne["Email"].lower():
                    resultats.append(ligne)
    return {"status": 200, "donnee": resultats}

def Liste_Contacts(donnee, demandeur):
    """
    Récupère l'intégralité de l'annuaire d'un utilisateur cible.
    Nécessite une vérification des droits d'accès.
    
    Args:
        donnee (dict): Contient 'proprietaire_cible'.
        demandeur (str): Nom de l'utilisateur qui demande la liste.
        
    Returns:
        dict: Liste complète des dictionnaires de contacts trouvés.
    """
    cible = donnee.get("proprietaire_cible")
    if not Verification_Droit(demandeur, cible):
        return {"status": 403, "message": "Accès refusé"}

    path = DOSSIER_ANNUAIRES / f"annuaire_{cible}.csv"
    if not path.exists():
        return {"status": 404, "message": "L'annuaire est Introuvable"}
    if reseau.connecter_serveur():
        with open(path, "r", encoding="utf-8") as fichier:
            return {"status": 200, "message": "Liste des contacts transférée au client","donnee": list(csv.DictReader(fichier))}
    else:
        return {"status": 503, "message": "Serveur hors ligne (Connexion perdue)"}

"""
--------------------------------------------------------------------------------------------------------
"""
def Modification_Contact(donnee, demandeur):
    """ 1
    Met à jour les informations d'un contact existant dans l'annuaire du demandeur.
    Remplace la ligne correspondante dans le fichier CSV.
    
    Args:
        donnee (dict): Contient le dictionnaire 'contact' mis à jour.
        demandeur (str): Nom du propriétaire de l'annuaire.
        
    Returns:
        dict: Message de succès ou d'erreur si le contact n'est pas trouvé.
    """
    contact_modifie = donnee.get("contact")
    path = DOSSIER_ANNUAIRES / f"annuaire_{demandeur}.csv"
    
    if not path.exists():
        return {"status": 404, "message": "Annuaire introuvable"}
    
    contacts = []
    modifie = False
    # ÉTAPE 1 : LECTURE
    with open(path, "r", encoding = "utf-8") as fichier:
        contenu = csv.DictReader(fichier)
        entete = contenu.fieldnames # On sauvegarde les noms de colonnes
        for ligne in contenu:
            # Si c'est le contact qu'on veut modifier...
            if ligne["Nom"] == contact_modifie["Nom"] and ligne["Prenom"] == contact_modifie["Prenom"]:
                contacts.append(contact_modifie) # ... on ajoute la NOUVELLE version
                modifie = True
            else:
                contacts.append(ligne) # ... sinon on garde l'ANCIENNE version
    
    if not modifie:
        return {"status": 404, "message": "Contact à modifier non trouvé"}
    # ÉTAPE 2 : ÉCRITURE (Écrasement)
    # Mode "w" (Write) : Efface tout le contenu précédent du fichier !
    with open(path, "w", newline="", encoding = "utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames = entete)
        writer.writeheader() # Réécrire les en-têtes (Nom, Prenom...)
        writer.writerows(contacts) # Réécrire toutes les données
        
    return {"status": 200, "message": "Contact mis à jour"}

def Suppression_Contact(donnee, demandeur):
    """ 2
    Supprime un contact spécifique de l'annuaire du demandeur en réécrivant le fichier CSV sans la ligne ciblée.
    
    Args:
        donnee (dict): Contient les identifiants du contact à supprimer.
        demandeur (str): Nom de l'utilisateur connecté.
        
    Returns:
        dict: Message de confirmation ou erreur 404.
    """
    cible = donnee.get("contact")
    path = DOSSIER_ANNUAIRES / f"annuaire_{demandeur}.csv"
    
    if not path.exists():
        return {"status": 404, "message": "Annuaire introuvable"}
    
    contacts_restants = []
    trouve = False
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for ligne in reader:
            if ligne["Nom"] == cible["Nom"] and ligne["Prenom"] == cible["Prenom"]:
                trouve = True
            else:
                contacts_restants.append(ligne)
    
    if not trouve:
        return {"status": 404, "message": "Contact introuvable"}
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(contacts_restants)
        
    return {"status": 200, "message": "Contact supprimé avec succès"}

def Suppression_Compte(donnee):
    """ 3
    Fonction administrative : Supprime un compte utilisateur, son fichier annuaire associé
    et nettoie toutes les permissions liées (données ou reçues) dans le fichier permissions.
    
    Args:
        donnee (dict): Contient 'nom_compte' à supprimer.
        
    Returns:
        dict: Message de succès (200) ou erreur si compte introuvable.
    """
    cible = donnee.get("nom_compte")
    
    comptes_restants = []
    trouve = False
    
    if FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for ligne in reader:
                if ligne["Nom"] == cible:
                    trouve = True
                else:
                    comptes_restants.append(ligne)

    if not trouve:
        return {"status": 404, "message": "Compte introuvable"}

    with open(FICHIER_COMPTES, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comptes_restants)

    path_annuaire = DOSSIER_ANNUAIRES / f"annuaire_{cible}.csv"
    path_annuaire.unlink(missing_ok=True)

    perms_restantes = []
    if FICHIER_PERMISSIONS.exists():
        with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            entete = next(reader, None)
            if entete:
                perms_restantes.append(entete)
            
            for ligne in reader:
                # ligne[0] = Proprietaire, ligne[1] = Utilisateur_Autorise
                if len(ligne) >= 2 and ligne[0] != cible and ligne[1] != cible:
                    perms_restantes.append(ligne)
        
        with open(FICHIER_PERMISSIONS, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(perms_restantes)

    return {"status": 200, "message": f"Compte {cible} et données supprimés"}

def Modification_Compte(donnee):
    """ 4
    Fonction administrative : Modifie le mot de passe ou le statut (rôle) d'un utilisateur existant.
    
    Args:
        donnee (dict): Contient 'nom_compte', 'nouveau_mdp' (optionnel) et 'nouveau_statut' (optionnel).
        
    Returns:
        dict: Message de confirmation de la mise à jour.
    """
    cible = donnee.get("nom_compte")
    nouveau_mdp = donnee.get("nouveau_mdp")
    nouveau_statut = donnee.get("nouveau_statut")

    if not FICHIER_COMPTES.exists():
        return {"status": 404, "message": "Fichier comptes introuvable"}

    comptes = []
    modifie = False

    with open(FICHIER_COMPTES, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for ligne in reader:
            if ligne["Nom"] == cible:
                if nouveau_mdp:
                    ligne["Mot_de_passe"] = nouveau_mdp
                if nouveau_statut:
                    ligne["Statut"] = nouveau_statut
                modifie = True
            comptes.append(ligne)

    if not modifie:
        return {"status": 404, "message": f"Compte '{cible}' introuvable"}

    with open(FICHIER_COMPTES, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comptes)

    return {"status": 200, "message": f"Compte '{cible}' mis à jour avec succès"}

def Infos_Admin():
    """ 5
    Fonction administrative : Génère des statistiques globales sur le serveur.
    Récupère pour chaque utilisateur : son rôle, le nombre de contacts dans son annuaire 
    et le nombre d'annuaires qu'il est autorisé à consulter.
    
    Returns:
        dict: Liste de dictionnaires contenant les statistiques.
    """
    stats = []
    nbr_annuaires_consultables = {}
    if FICHIER_PERMISSIONS.exists():
        with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for ligne in reader:
                user = ligne.get("Utilisateur_Autorise")
                if user:
                    nbr_annuaires_consultables[user] = nbr_annuaires_consultables.get(user, 0) + 1

    if FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for compte in reader:
                nom = compte["Nom"]
                
                path_cible = DOSSIER_ANNUAIRES / f"annuaire_{nom}.csv"
                nb_contacts = 0
                
                if path_cible.exists():
                    with open(path_cible, "r", encoding="utf-8") as fa:
                        total_lignes = sum(1 for _ in fa)
                        nb_contacts = max(0, total_lignes - 1)
                
                stats.append({
                    "Nom": nom,
                    "Statut": compte["Statut"],
                    "Nb_Contacts": nb_contacts,
                    "Nb_Annuaires": nbr_annuaires_consultables.get(nom, 0)
                })
                
    return {"status": 200, "message": "Tableau récapitulatif des données Serveur", "donnee": stats}

def Liste_Proprio(demandeur):
    """ 6
    Renvoie la liste des propriétaires d'annuaires que le demandeur a le droit de consulter.
    Utilise Verification_Droit en mode liste.
    
    Returns:
        dict: Liste de noms d'utilisateurs.
    """
    liste = Verification_Droit(demandeur)
    return {"status": 200, "message": "Affichage de la liste des propriétaires", "donnee": liste}

def Liste_Droit(demandeur):
    """ 7
    Renvoie la liste des utilisateurs à qui le demandeur a donné la permission de voir son annuaire.
    
    Returns:
        dict: Liste de noms d'utilisateurs.
    """
    liste = []
    if FICHIER_PERMISSIONS.exists():
        with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as fichier:
            for ligne in csv.DictReader(fichier):
                if ligne["Proprietaire"] == demandeur:
                    liste.append(ligne["Utilisateur_Autorise"])
    return {"status": 200, "message": "Liste des utilisteurs à qui vous avez donné l'accès à votre annuaire", "donnee": liste}

def Verification_Connexion(donnee):
    """ 8
    Vérifie la correspondance Nom/Mot de passe dans le fichier CSV des comptes.
    
    Args:
        donnee (dict): Identifiants de connexion.
        
    Returns:
        dict: Status 200 avec le rôle de l'utilisateur si valide, sinon 401.
    """
    if FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "r", encoding="utf-8") as fichier:
            for ligne in csv.DictReader(fichier):
                if ligne["Nom"] == donnee["nom"] and ligne["Mot_de_passe"] == donnee["mdp"]:
                    return {"status": 200, "message": "Connexion Établie", "role": ligne["Statut"]}
    return {"status": 401, "message": "Connexion Échouée"}

def Verification_Droit(demandeur, cible=None):
    """ 9
    Vérifie les permissions d'accès aux annuaires.
    
    Modes:
    1. Si 'cible' est fourni : Vérifie si 'demandeur' a le droit de voir l'annuaire de 'cible' (Retourne booléen).
    2. Si 'cible' est None : Retourne la liste de tous les propriétaires que 'demandeur' peut consulter (Retourne liste).
    
    Le propriétaire a toujours accès à son propre annuaire.
    """
    # --- Mode 1 : Vérification d'un accès spécifique ---
    # On a toujours le droit de voir notre propre annuaire.
    if cible is not None:
        if demandeur == cible: 
            return True
        # Si on regarde chez quelqu'un d'autre, on check le fichier permissions.csv
        if FICHIER_PERMISSIONS.exists():
            with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as fichier:
                for ligne in csv.DictReader(fichier):
                    # On cherche la ligne exacte : Proprietaire=Cible ET Autorisé=Demandeur
                    if ligne["Proprietaire"] == cible and ligne["Utilisateur_Autorise"] == demandeur:
                        return True
        return False # Si rien trouvé, accès refusé par défaut

    # --- Mode 2 : Récupération de tous les droits ---
    else:
        liste = []
        if FICHIER_PERMISSIONS.exists():
            with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as fichier:
                for ligne in csv.DictReader(fichier):
                    if ligne["Utilisateur_Autorise"] == demandeur:
                        liste.append(ligne["Proprietaire"])
        return liste

def Gestion_Permission(donnee, demandeur):
    """ 10
    Ajoute ou retire une permission d'accès dans le fichier 'permissions.csv'.
    Empêche un utilisateur de se cibler lui-même.
    
    Args:
        donnee (dict): Contient 'utilisateur_cible' et le type d'action ('donner' ou autre pour retirer).
        demandeur (str): L'utilisateur qui gère ses permissions.
        
    Returns:
        dict: Confirmation de l'action.
    """
    cible = donnee.get("utilisateur_cible")
    action = donnee.get("type")
    colonnes = []
    if FICHIER_PERMISSIONS.exists():
        with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as fichier:
            colonnes = list(csv.reader(fichier))
    
    nouveau = [ligne for ligne in colonnes if not (ligne[0] == demandeur and ligne[1] == cible)]
    if demandeur != cible:
        if action == "donner":
            nouveau.append([demandeur, cible])
    else:
        return {"status": 401, "message": "Vous n’avez pas le droit de vous cibler vous-même"}
    
    with open(FICHIER_PERMISSIONS, "w", newline="", encoding="utf-8") as fichier:
        csv.writer(fichier).writerows(nouveau)
    return {"status": 200, "message": "Modification Effectuée"}

def Liste_Comptes():
    """ 11
    Récupère la liste simple de tous les noms d'utilisateurs inscrits sur le serveur.
    
    Returns:
        dict: Liste de chaînes de caractères (noms).
    """
    comptes = []
    if FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "r", encoding="utf-8") as fichier:
            reader = csv.DictReader(fichier)
            for ligne in reader:
                comptes.append(ligne["Nom"])
    return {"status": 200, "message": "Affichage de la liste des comptes existants", "donnee": comptes}

"""
---------------------------------------------------------------------------------------------------------
"""

def recevoir_pdu(requete):
    """
    Fonction centrale de routage.
    Analyse l'action demandée dans le PDU, appelle la fonction correspondante,
    et formate la réponse JSON. Gère aussi l'affichage des logs côté serveur.
    
    Args:
        requete (dict): Le PDU reçu (Action, Demandeur, Corps).
        
    Returns:
        dict: Le PDU de réponse (Status, Message, Donnée).
    """
    # 1. Extraction des métadonnées de la requête
    # On note l'heure pour les logs serveur (traçabilité).
    date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    action = requete.get("action") # Quoi faire ? (ex: "AJOUT_CONTACT")
    demandeur = requete.get("demandeur") # Qui demande ? (ex: "Abasse")
    corps = requete.get("corps", {}) # Avec quelles données ? (ex: {"Nom": "Ayyub", ...})
    
    # Réponse par défaut si l'action n'est pas reconnue
    reponse = {"status": 400, "message": "Action inconnue"}

    # 2. Aiguillage (Routing)
    # On compare le mot-clé 'action' et on dirige vers la fonction métier correspondante.
    if action == "CONNEXION":
        # Vérifie login/mdp dans comptes.csv
        reponse = Verification_Connexion(corps)
        identifiant = corps.get("nom", "Inconnu")
        
    elif action == "CREATION_COMPTE":
        # Crée une ligne dans comptes.csv + un fichier vide annuaire_X.csv
        reponse = Creation_Compte(corps)
        identifiant = corps.get("nom", "Nouveau Compte")
        
    elif action == "AJOUT_CONTACT":
        # Ajoute une ligne dans annuaire_demandeur.csv
        reponse = Ajout_Contact(corps, demandeur)
        identifiant = demandeur

    elif action == "RECHERCHE_CONTACT":
        # Lit annuaire_cible.csv et filtre les résultats
        # Note : demandeur est passé en paramètre pour vérifier les droits d'abord !
        reponse = Recherche_Contact(corps, demandeur)
        identifiant = demandeur
        cible = corps.get("proprietaire_cible", None)

    elif action == "LISTE_CONTACTS":
        # Le client veut lister un annuaire entier.
        # Note : On passe 'demandeur' à la fonction pour vérifier s'il a le droit
        reponse = Liste_Contacts(corps, demandeur)
        identifiant = demandeur
        cible = corps.get("proprietaire_cible", None)

    elif action == "GERER_PERMISSION":
        # Action de partage : Donner ou retirer le droit de voir son annuaire.
        # C'est une modification du fichier 'permissions.csv'.
        reponse = Gestion_Permission(corps, demandeur)
        identifiant = demandeur

    elif action == "MODIF_CONTACT":
        # Demande de mise à jour d'un contact existant (ex: changement de numéro).
        # Le serveur va réécrire le fichier CSV de l'utilisateur.
        reponse = Modification_Contact(corps, demandeur)
        identifiant = demandeur

    elif action == "SUPPR_CONTACT":
        # Demande de suppression.
        # Le serveur va chercher le contact et réécrire le fichier sans lui.
        reponse = Suppression_Contact(corps, demandeur)
        identifiant = demandeur

    elif action == "LISTE_PROPRIO":
        # "Qui ai-je le droit de regarder ?"
        # Sert à remplir le menu "Annuaire Consultable" côté client.
        reponse = Liste_Proprio(demandeur)
        identifiant = demandeur

    elif action == "LISTE_COMPTES":
        # "Qui existe sur ce serveur ?"
        # Sert à l'autocomplétion ou pour choisir à qui donner une permission.
        reponse = Liste_Comptes() # Pas besoin d'arguments, c'est public/global.
        identifiant = demandeur

    elif action == "LISTE_DROIT":
        # "Qui a le droit de me regarder ?"
        # Sert à afficher la liste dans le menu "Gérer Permissions" -> "Retirer".
        reponse = Liste_Droit(demandeur)
        identifiant = demandeur

    elif action == "SUPPRESSION_COMPTE":
        # DANGER : Supprime une ligne dans comptes.csv, supprime le fichier annuaire_X.csv 
        # et nettoie permissions.csv. Irréversible.
        reponse = Suppression_Compte(corps)
        identifiant = demandeur

    elif action == "MODIF_COMPTE":
        # Changement de mot de passe ou de rôle (Admin/User).
        # Appel la fonction qui modifie 'comptes.csv'.
        reponse = Modification_Compte(corps)
        identifiant = demandeur

    elif action == "INFOS_ADMIN":
        # Demande de statistiques globales (Tableau de bord).
        # Le serveur scanne tous les fichiers pour compter les lignes.
        reponse = Infos_Admin()
        identifiant = demandeur
    
    else:
        # Si l'action n'est dans aucun des 'elif', on ne sait pas quoi faire.
        identifiant = "Inconnu"

    # 3. Logging (Journalisation)
    # Le serveur doit garder une trace de ce qu'il fait dans sa propre console.
    status = reponse.get("status")
    message = reponse.get("message")
    # Code couleur pour lecture rapide (Vert = OK, Rouge = Problème)
    if status in [200, 201]:
        tag = "\033[92m[SUCCÈS]\033[0m" # Vert
    else:
        tag = "\033[91m[ERREUR]\033[0m" # Rouge
    # Affichage formaté : QUI a fait QUOI, sur QUI, et quel est le RÉSULTAT.
    if cible == None:
        print(f"{date} {tag} Action: {action} | User: {identifiant} ")
        print(f"\t\t\t└── message: {message}")
    else:
        print(f"{date} {tag} Action: {action} | User: {identifiant} | Cible: {cible}")
        print(f"\t\t\t└── message: {message}")
    # 4. Retour
    # On renvoie le dictionnaire réponse qui sera converti en JSON pour le client.
    return reponse

def menu_serveur():
    """
    Boucle principale du serveur.
    1. Initialise l'environnement (fichiers/dossiers).
    2. Affiche le menu console administrateur.
    3. Surveille la présence du fichier 'pdu_requete.json' pour traiter les demandes entrantes.
    4. Gère l'écriture de 'pdu_reponse.json'.
    """
    # 1. Initialisation
    reseau.creer_serveur() # Crée les dossiers si absents
            
    while True:
        taille = 40
        titre = "=== CONSOLE SERVEUR ==="
        options = [
            "1. Démarrer le Serveur (Écoute)",
            "2. Réinitialiser les données(DANGER)",
            "0. Quitter"
        ]
        mes_fonctions.deco_console(titre, taille, options)
        choix = input("Votre choix > ")
        
        if choix == "1":
            # Création du "Témoin" : Indique aux clients que le serveur est allumé.
            with open(reseau.FICHIER_TEMOIN, "w") as f:
                f.write("ONLINE")
            print("[RESEAU] Serveur ouvert aux connexions.")
            print("\n" + "="*40)
            print(" SERVEUR EN LIGNE (Ctrl+C pour stopper)")
            print("="*40)
            
            try:
                # BOUCLE INFINIE D'ÉCOUTE
                while True:
                    # 2. Polling : Est-ce qu'une requête est arrivée ?
                    if reseau.FICHIER_REQUETE.exists():
                        try:
                            # A. Lecture de la requête (pdu_requete.json)
                            with open(reseau.FICHIER_REQUETE, "r", encoding="utf-8") as f:
                                requete = json.load(f)
                            # B. Traitement
                            reponse = recevoir_pdu(requete)
                            # C. Nettoyage : On supprime la requête pour dire "J'ai bien reçu"
                            # C'est important pour éviter de traiter 2 fois la même demande.
                            os.remove(reseau.FICHIER_REQUETE)
                            # D. Envoi de la réponse (pdu_reponse.json)
                            with open(reseau.FICHIER_REPONSE, "w", encoding="utf-8") as f:
                                json.dump(reponse, f, indent=4)
                                
                        except Exception as e:
                            # Filets de sécurité : Si le JSON est corrompu ou illisible, le serveur ne doit PAS crasher. Il log l'erreur et continue.
                            print(f"[ERREUR] {e}")
                            if reseau.FICHIER_REQUETE.exists():
                                os.remove(reseau.FICHIER_REQUETE)
                    # Petite pause pour ne pas surcharger le processeur (CPU) à faire des boucles vides.
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                # Gestion propre de l'arrêt avec Ctrl+C
                print("\nArrêt du serveur...")
            finally:
                # Nettoyage final (suppression du témoin ONLINE)
                reseau.deconnecter_serveur()
                time.sleep(1.5)
        elif choix == "2":
            conf = input("Tapez 'OUI' pour tout supprimer : ")
            if conf in ["OUI", "oui", "O", "o"]:
                shutil.rmtree(reseau.DOSSIER_DATA)
                print("Données effacées.\n")
                reseau.creer_serveur()
            else:
                print("Annulation...")
                time.sleep(1.5)
        elif choix == "0":
            reseau.deconnecter_serveur()
            break
        
        mes_fonctions.clear_console()

if __name__ == "__main__":
    menu_serveur()