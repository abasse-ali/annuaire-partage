"""
Serveur
"""

import csv
from pathlib import Path

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
    contact = donnee.get("contact")
    if not (contact.get("Nom") and contact.get("Prenom") and contact.get("Email")):
        return {"status": 400, "message": "Nom/Prénom/Email requis"}

    path = DOSSIER_ANNUAIRES / f"annuaire_{demandeur}.csv"
    if not path.exists(): return {"status": 404, "message": "Annuaire introuvable"}

    lignes = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        lignes = list(reader)
        for ligne in lignes:
            if ligne["Nom"] == contact["Nom"] and ligne["Prenom"] == contact["Prenom"]:
                 return {"status": 409, "message": "Ce contact existe déjà"}
    
    with open(path, "a", newline="", encoding="utf-8") as fichier:
        w = csv.DictWriter(fichier, fieldnames=["Nom", "Prenom", "Telephone", "Adresse", "Email"])
        w.writerow(contact)
    return {"status": 200, "message": "Contact ajouté"}

def Recherche_Contact(donnee, demandeur):
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
    cible = donnee.get("proprietaire_cible")
    if not Verification_Droit(demandeur, cible):
        return {"status": 403, "message": "Accès refusé"}

    path = DOSSIER_ANNUAIRES / f"annuaire_{cible}.csv"
    if not path.exists(): return {"status": 404, "message": "Introuvable"}
    
    with open(path, "r", encoding="utf-8") as fichier:
        return {"status": 200, "donnee": list(csv.DictReader(fichier))}

def Modification_Contact(donnee, demandeur):
    contact_modifie = donnee.get("contact")
    path = DOSSIER_ANNUAIRES / f"annuaire_{demandeur}.csv"
    
    if not path.exists():
        return {"status": 404, "message": "Annuaire introuvable"}
    
    contacts = []
    modifie = False
    
    with open(path, "r", encoding = "utf-8") as fichier:
        contenu = csv.DictReader(fichier)
        entete = contenu.fieldnames
        for ligne in contenu:
            if ligne["Nom"] == contact_modifie["Nom"] and ligne["Prenom"] == contact_modifie["Prenom"]:
                contacts.append(contact_modifie)
                modifie = True
            else:
                contacts.append(ligne)
    
    if not modifie:
        return {"status": 404, "message": "Contact à modifier non trouvé"}

    with open(path, "w", newline="", encoding = "utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames = entete)
        writer.writeheader()
        writer.writerows(contacts)
        
    return {"status": 200, "message": "Contact mis à jour"}

"""
--------------------------------------------------------------------------------------------------------
"""
import csv
from pathlib import Path

# Plus besoin de 'import os'

def Suppression_Compte(donnee):
    cible = donnee.get("nom_compte")
    
    # 1. Vérifier si le compte existe et préparer la liste filtrée
    comptes_restants = []
    trouve = False
    
    # On suppose que FICHIER_COMPTES est un objet Path
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

    # 2. Réécrire le fichier des comptes
    with open(FICHIER_COMPTES, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comptes_restants)

    # 3. Supprimer l'annuaire associé AVEC PATHLIB
    # On utilise l'opérateur / pour joindre les chemins proprement
    path_annuaire = DOSSIER_ANNUAIRES / f"annuaire_{cible}.csv"
    
    # .unlink() remplace os.remove()
    # missing_ok=True évite une erreur si le fichier n'existe pas déjà (Python 3.8+)
    try:
        path_annuaire.unlink(missing_ok=True)
    except FileNotFoundError:
        pass # Anciennes versions de python sans missing_ok

    # 4. Nettoyer les permissions
    perms_restantes = []
    if FICHIER_PERMISSIONS.exists():
        with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            entete = next(reader, None)
            if entete:
                perms_restantes.append(entete)
            
            for ligne in reader:
                # ligne[0] = Proprietaire, ligne[1] = Utilisateur_Autorise
                # On garde la ligne si la cible n'est NI propriétaire NI autorisé
                if len(ligne) >= 2 and ligne[0] != cible and ligne[1] != cible:
                    perms_restantes.append(ligne)
        
        with open(FICHIER_PERMISSIONS, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(perms_restantes)

    return {"status": 200, "message": f"Compte {cible} et données supprimés"}

def Infos_Admin():
    """Récupère: Nom, Role, Nb Contacts, Nb d'annuaires consultables"""
    stats = []
    
    # 1. Compter les droits d'accès via le fichier permissions
    droits_acces = {} 
    if FICHIER_PERMISSIONS.exists():
        with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for ligne in reader:
                user = ligne.get("Utilisateur_Autorise")
                if user:
                    droits_acces[user] = droits_acces.get(user, 0) + 1

    # 2. Parcourir les comptes et compter les fichiers
    if FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for compte in reader:
                nom = compte["Nom"]
                
                # Utilisation de pathlib pour le chemin
                path_cible = DOSSIER_ANNUAIRES / f"annuaire_{nom}.csv"
                nb_contacts = 0
                
                if path_cible.exists():
                    # Petite astuce mémoire : on compte les lignes sans charger tout le fichier
                    # -1 pour l'entête
                    with open(path_cible, "r", encoding="utf-8") as fa:
                         # sum(1 for _ in fa) compte les lignes efficacement
                        total_lignes = sum(1 for i in fa)
                        nb_contacts = max(0, total_lignes - 1)
                
                stats.append({
                    "Nom": nom,
                    "Statut": compte["Statut"],
                    "Nb_Contacts": nb_contacts,
                    "Droits_Consultation": droits_acces.get(nom, 0)
                })
                
    return {"status": 200, "donnee": stats}
"""
---------------------------------------------------------------------------------------------------------
"""
def Liste_Proprio(demandeur):
    liste = Verification_Droit(demandeur)
    return {"status": 200, "message": "Succès", "donnee": liste}

def Liste_Droit(demandeur):
    liste = []
    if FICHIER_PERMISSIONS.exists():
        with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as fichier:
            for ligne in csv.DictReader(fichier):
                if ligne["Proprietaire"] == demandeur:
                    liste.append(ligne["Utilisateur_Autorise"])
    return {"status": 200, "message": "Succès", "donnee": liste}

def Verification_Connexion(donnee):
    if FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "r", encoding="utf-8") as fichier:
            for ligne in csv.DictReader(fichier):
                if ligne["Nom"] == donnee["nom"] and ligne["Mot_de_passe"] == donnee["mdp"]:
                    return {"status": 200, "role": ligne["Statut"]}
    return {"status": 401, "message": "Connexion Échouée"}

def Verification_Droit(demandeur, cible=None):
    """
    Mode 1 : Si 'cible' est fourni, renvoie True/False (Booléen).
    Mode 2 : Si 'cible' est None, renvoie la liste des propriétaires (Liste).
    """
    # --- Mode 1 : Vérification d'un accès spécifique ---
    if cible is not None:
        if demandeur == cible: 
            return True # On a toujours accès à soi-même
        
        if FICHIER_PERMISSIONS.exists():
            with open(FICHIER_PERMISSIONS, "r", encoding="utf-8") as fichier:
                for ligne in csv.DictReader(fichier):
                    if ligne["Proprietaire"] == cible and ligne["Utilisateur_Autorise"] == demandeur:
                        return True
        return False

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
    comptes = []
    if FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "r", encoding="utf-8") as fichier:
            reader = csv.DictReader(fichier)
            for ligne in reader:
                comptes.append(ligne["Nom"])
    return {"status": 200, "donnee": comptes}