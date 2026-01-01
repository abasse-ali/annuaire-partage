"""
Reseau
"""

import json
import csv
import serveur

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

FICHIER_REQUETE = serveur.DOSSIER_DATA / "pdu_requete.json"
FICHIER_REPONSE = serveur.DOSSIER_DATA / "pdu_reponse.json"

ETAT = {"actif": False, "connecte": False}

def creer_serveur():
    print("Activation Serveur...")
    serveur.DOSSIER_DATA.mkdir(exist_ok=True)
    serveur.DOSSIER_ANNUAIRES.mkdir(exist_ok=True)
    
    if not serveur.FICHIER_COMPTES.exists():
        with open(serveur.FICHIER_COMPTES, "w", encoding = "utf-8", newline="") as fichier: 
            csv.writer(fichier).writerow(["Nom", "Statut", "Mot_de_passe"])
    
    if not serveur.FICHIER_PERMISSIONS.exists():
        with open(serveur.FICHIER_PERMISSIONS, "w", encoding = "utf-8", newline="") as fichier:
             csv.writer(fichier).writerow(["Proprietaire", "Utilisateur_Autorise"])
    
    ETAT["actif"] = True

def connecter_serveur():
    if ETAT["actif"]:
        ETAT["connecte"] = True
        print("CLient connecté au Serveur")
    return ETAT["connecte"]

def deconnecter_serveur():
    ETAT["connecte"] = False
    print("Déconexion...")
    
def envoyer_PDU(action, corps, utilisateur_courant=None):
    pdu = {"action": action, "demandeur": utilisateur_courant, "corps": corps}
    
    if not ETAT["connecte"]:
        return {"status": 500, "message": "Non connecté"}

    with open(FICHIER_REQUETE, "w", encoding="utf-8") as fichier:
        json.dump(pdu, fichier, indent=4)
    
    recevoir_PDU(FICHIER_REQUETE, FICHIER_REPONSE)
    
    if FICHIER_REPONSE.exists():
        try:
            with open(FICHIER_REPONSE, "r", encoding="utf-8") as fichier:
                return json.load(fichier)
        except json.JSONDecodeError:
            return {"status": 500, "message": "Erreur lecture réponse JSON"}
    return {"status": 500, "message": "Pas de réponse"}
    
def recevoir_PDU(chemin_requete, chemin_reponse):
    if not chemin_requete.exists():
        return

    try:
        with open(chemin_requete, "r", encoding="utf-8") as fichier:
            requete = json.load(fichier)
    except json.JSONDecodeError:
        return
    
    action = requete.get("action")
    demandeur = requete.get("demandeur")
    corps = requete.get("corps", {})
    
    if action == "CONNEXION": reponse = serveur.Verification_Connexion(corps)
    elif action == "CREATION_COMPTE": reponse = serveur.Creation_Compte(corps)
    elif action == "AJOUT_CONTACT": reponse = serveur.Ajout_Contact(corps, demandeur)
    elif action == "RECHERCHE_CONTACT": reponse = serveur.Recherche_Contact(corps, demandeur)
    elif action == "LISTE_CONTACTS": reponse = serveur.Liste_Contacts(corps, demandeur)
    elif action == "GERER_PERMISSION": reponse = serveur.Gestion_Permission(corps, demandeur)
    elif action == "MODIF_CONTACT": reponse = serveur.Modification_Contact(corps, demandeur)
    elif action == "LISTE_PROPRIO": reponse = serveur.Liste_Proprio(demandeur)
    elif action == "LISTE_COMPTES" : reponse = serveur.Liste_Comptes()
    elif action == "LISTE_DROIT": reponse = serveur.Liste_Droit(demandeur)
    elif action == "SUPPRESSION_COMPTE": reponse = serveur.Suppression_Compte(corps)
    elif action == "INFOS_ADMIN": reponse = serveur.Infos_Admin()
    else: reponse = {"status": 400, "message": "Action inconnue"}

    with open(chemin_reponse, "w", encoding="utf-8") as fichier:
        json.dump(reponse, fichier, indent=4)