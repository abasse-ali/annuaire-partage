import csv
import shutil
from pathlib import Path

# On importe ton module serveur
import serveur

# --- CONFIGURATION DE L'ENVIRONNEMENT DE TEST ---
print("--- INITIALISATION DE L'ENVIRONNEMENT DE TEST ---")
dossier_test = Path("test_env")

# On redirige les variables du serveur vers ce dossier temporaire
serveur.DOSSIER_DATA = dossier_test
serveur.FICHIER_COMPTES = dossier_test / "comptes.csv"
serveur.FICHIER_PERMISSIONS = dossier_test / "permissions.csv"
serveur.DOSSIER_ANNUAIRES = dossier_test / "annuaires"
fichier_temoin = dossier_test / ".server_online"

def creer_serveur():
    """
    Initialise l'architecture du serveur au démarrage.
    Crée les dossiers (donnee_serveur, annuaires) et les fichiers CSV vides s'ils n'existent pas.
    Crée un compte Administrateur par défaut si aucun admin n'est détecté.
    """
    serveur.DOSSIER_DATA.mkdir(exist_ok=True)
    serveur.DOSSIER_ANNUAIRES.mkdir(exist_ok=True)
    
    if not serveur.FICHIER_COMPTES.exists():
        with open(serveur.FICHIER_COMPTES, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(["Nom", "Statut", "Mot_de_passe"])
    
    if not serveur.FICHIER_PERMISSIONS.exists():
        with open(serveur.FICHIER_PERMISSIONS, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(["Proprietaire", "Utilisateur_Autorise"])

# Nettoyage préventif et création des dossiers
if dossier_test.exists():
    shutil.rmtree(dossier_test)
creer_serveur() # Cette fonction du serveur va créer les fichiers vides

# Fonction utilitaire pour afficher les résultats proprement
def verifier(nom_test, reponse_recue):
    status_recu = reponse_recue.get("status")
    print(f"TEST: {nom_test}")
    print(f"   (Status: {status_recu})")
    print(f"      Message: {reponse_recue.get('message')}")
    print("-" * 50)


# ==========================================
# 1. TEST DE CREATION_COMPTE
# ==========================================
print("\n=== 1. TEST CREATION_COMPTE ===")

# Cas 1 : Création normale
donnee_user = {"nom": "TestUser", "mot_de_passe": "hash123", "statut": "utilisateur"}
rep = serveur.Creation_Compte(donnee_user)
verifier("Création nouveau compte", rep)

# Cas 2 : Création doublon (Doit échouer)
rep = serveur.Creation_Compte(donnee_user)
verifier("Tentative création doublon", rep)


# ==========================================
# 2. TEST DE AJOUT_CONTACT
# ==========================================
print("\n=== 2. TEST AJOUT_CONTACT ===")
demandeur = "TestUser"
contact_valide = {
    "Nom": "DUPONT", "Prenom": "Jean", 
    "Telephone": "0600000000", "Adresse": "Paris", "Email": "jean@mail.com"
}

# Cas 1 : Ajout valide
rep = serveur.Ajout_Contact({"contact": contact_valide}, demandeur)
verifier("Ajout contact valide", rep)

# Cas 2 : Champs manquants
contact_incomplet = {"Nom": "DURAND"} # Pas de prénom ni mail
rep = serveur.Ajout_Contact({"contact": contact_incomplet}, demandeur)
verifier("Ajout contact incomplet", rep)

# Cas 3 : Ajout doublon
rep = serveur.Ajout_Contact({"contact": contact_valide}, demandeur)
verifier("Ajout contact existant", rep)

# ==========================================
# 3. TEST DE RECHERCHE_CONTACT
# ==========================================
print("\n=== 3. TEST RECHERCHE_CONTACT ===")
# Note: On triche un peu sur Verification_Droit car on n'a pas setup les permissions,
# mais comme on cherche dans son propre annuaire (cible = demandeur), ça passe toujours True.

# Cas 1 : Recherche fructueuse
donnee_rech = {"proprietaire_cible": "TestUser", "recherche": "jean"}
rep = serveur.Recherche_Contact(donnee_rech, demandeur)

# Ici on vérifie le status ET si on a trouvé des données
if rep["status"] == 200 and len(rep["donnee"]) == 1:
    print(f"TEST: Recherche 'jean' -> SUCCÈS (Trouvé: {rep['donnee'][0]['Nom']})")
else:
    print(f"TEST: Recherche 'jean' -> ÉCHEC (Res: {rep})")
print("-" * 50)

# Cas 2 : Recherche infructueuse
donnee_rech_vide = {"proprietaire_cible": "TestUser", "recherche": "xyz"}
rep = serveur.Recherche_Contact(donnee_rech_vide, demandeur)

if rep["status"] == 200 and len(rep["donnee"]) == 0:
    print(f"TEST: Recherche 'xyz' -> SUCCÈS (Liste vide renvoyée)")
else:
    print(f"TEST: Recherche 'xyz' -> ÉCHEC")
print("-" * 50)


# ==========================================
# 4. TEST DE LISTE_CONTACTS
# ==========================================
print("\n=== 4. TEST LISTE_CONTACTS ===")

# Cas 1 : Récupération liste complète
donnee_liste = {"proprietaire_cible": "TestUser"}
rep = serveur.Liste_Contacts(donnee_liste, demandeur)
if rep["status"] == 200 and len(rep["donnee"]) >= 1:
    print(f"TEST: Récupération liste complète -> SUCCÈS (status: {rep['status']}, {len(rep['donnee'])} contacts)")
else:
    print(f"TEST: Récupération liste complète -> ÉCHEC (Status: {rep.get('status')}, message: {rep.get('message')}) ")
print("-" * 50)

# Cas 2 : Récupération liste d'un utilisateur inexistant
donnee_liste = {"proprietaire_cible": "Jean"} # Compte inexistant
rep = serveur.Liste_Contacts(donnee_liste, demandeur)
if rep["status"] == 200 and len(rep["donnee"]) >= 1:
    print(f"TEST: Récupération liste complète -> SUCCÈS (status: {rep['status']}, {len(rep['donnee'])} contacts)")
else:
    print(f"TEST: Récupération liste complète -> ÉCHEC (Status: {rep.get('status')}, message: {rep.get('message')})")
print("-" * 50)

# ==========================================
# 5. TEST DE MODIFICATION_CONTACT
# ==========================================
print("\n=== 5. TEST MODIFICATION_CONTACT ===")

contact_modifie = {
    "Nom": "DUPONT", "Prenom": "Jean", # Clés d'identification
    "Telephone": "0799999999", "Adresse": "Lyon", "Email": "new@mail.com" # Nouvelles valeurs
}

rep = serveur.Modification_Contact({"contact": contact_modifie}, demandeur)
verifier("Modification contact existant", rep)

# Vérification que la modif est réelle
rep_verif = serveur.Recherche_Contact({"proprietaire_cible": "TestUser", "recherche": "lyon"}, demandeur)
if rep_verif["donnee"] and rep_verif["donnee"][0]["Adresse"] == "Lyon":
    print("   -> Vérification données : L'adresse est bien 'Lyon'")
else:
    print("   -> Vérification données : La modification n'a pas été enregistrée")


# ==========================================
# 6. TEST DE SUPPRESSION_CONTACT
# ==========================================
print("\n=== 6. TEST SUPPRESSION_CONTACT ===")

contact_a_suppr = {"Nom": "DUPONT", "Prenom": "Jean"}

rep = serveur.Suppression_Contact({"contact": contact_a_suppr}, demandeur)
verifier("Suppression contact existant", rep)

# Essai de suppression d'un contact qui n'existe plus
rep = serveur.Suppression_Contact({"contact": contact_a_suppr}, demandeur)
verifier("Suppression contact inexistant", rep)

# ==========================================
# 7. TEST DE SUPPRESSION_COMPTE
# ==========================================
print("\n=== 7. TEST SUPPRESSION_COMPTE ===")

rep = serveur.Suppression_Compte({"nom_compte": "TestUser"})
verifier("Suppression compte utilisateur", rep)

# Vérification que le fichier annuaire est bien parti
path_annuaire = serveur.DOSSIER_ANNUAIRES / "annuaire_TestUser.csv"
if not path_annuaire.exists():
    print("   -> Vérification fichier : Le fichier annuaire a bien été supprimé")
else:
    print("   -> Vérification fichier : Le fichier annuaire existe encore")

# Essai sur compte inconnu
rep = serveur.Suppression_Compte({"nom_compte": "Fantome"})
verifier("Suppression compte inconnu", rep)

# --- NETTOYAGE FINAL ---
print("\n--- FIN DES TESTS ---")
# Décommenter la ligne suivante si tu veux supprimer le dossier test à la fin
shutil.rmtree(dossier_test)
print("Environnement de test nettoyé.")