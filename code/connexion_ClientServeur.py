"""
Reseau
"""

import os
import csv
import json
import time
from pathlib import Path
from hashlib import sha512

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

DOSSIER_DATA = Path("donnee_serveur")

FICHIER_TEMOIN = DOSSIER_DATA / ".server_online"

FICHIER_REQUETE = DOSSIER_DATA / "pdu_requete.json"
FICHIER_REPONSE = DOSSIER_DATA / "pdu_reponse.json"

FICHIER_COMPTES = DOSSIER_DATA / "comptes.csv"
FICHIER_PERMISSIONS = DOSSIER_DATA / "permissions.csv"
DOSSIER_ANNUAIRES = DOSSIER_DATA / "annuaires" 

def creer_serveur():
    """

    """
    DOSSIER_DATA.mkdir(exist_ok=True)
    DOSSIER_ANNUAIRES.mkdir(exist_ok=True)
    
    if not FICHIER_COMPTES.exists():
        with open(FICHIER_COMPTES, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(["Nom", "Statut", "Mot_de_passe"])
    
    if not FICHIER_PERMISSIONS.exists():
        with open(FICHIER_PERMISSIONS, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(["Proprietaire", "Utilisateur_Autorise"])

    ya_admin = False
    with open(FICHIER_COMPTES, "r", encoding="utf-8") as f:
        contenu = csv.DictReader(f)
        for ligne in contenu:
            if ligne["Statut"] == "administrateur":
                ya_admin = True
                break
            
    if not ya_admin:
        print("Initialisation d'un compte Administrateur par défaut...")
        
        nom_defaut = "aoun"
        mdp_defaut = sha512("stri26".encode()).hexdigest()
        statut_defaut = "administrateur"
        
        with open(FICHIER_COMPTES, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([nom_defaut, statut_defaut, mdp_defaut])
            
        annuaire_admin = DOSSIER_ANNUAIRES / f"annuaire_{nom_defaut}.csv"
        with open(annuaire_admin, "w", encoding="utf-8") as f:
            f.write("Nom,Prenom,Telephone,Adresse,Email\n")
            
        print(f"Compte '{nom_defaut}' (Admin) créé avec succès.")
def connecter_serveur():
    """
    
    """
    if FICHIER_TEMOIN.exists():
        return True
    return False

def deconnecter_serveur():
    """
    
    """
    if FICHIER_TEMOIN.exists():
        os.remove(FICHIER_TEMOIN)
    print("[RESEAU] Serveur fermé.")

def envoyer_PDU(action, corps, utilisateur_courant=None):
    """
    
    """
    pdu = {"action": action, "demandeur": utilisateur_courant, "corps": corps}
    
    if not FICHIER_TEMOIN.exists():
         return {"status": 503, "message": "Serveur hors ligne (Connexion perdue)"}

    if FICHIER_REPONSE.exists():
        os.remove(FICHIER_REPONSE)
            
    try:
        with open(FICHIER_REQUETE, "w", encoding="utf-8") as fichier:
            json.dump(pdu, fichier, indent=4)
            
        timeout = 10
        debut = time.time()
        while not FICHIER_REPONSE.exists():
            time.sleep(0.1)
            if time.time() - debut > timeout:
                return {"status": 504, "message": "Serveur ne répond pas"}
                
        time.sleep(0.1)
        with open(FICHIER_REPONSE, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
            
    except Exception as e:
        return {"status": 500, "message": f"Erreur: {e}"}