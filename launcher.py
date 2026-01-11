import time
import sys
import platform
import subprocess
from pathlib import Path

def lancer_app():
    systeme = platform.system()
    
    # Récupère le chemin du dossier où se trouve ce script (launcher.py)
    dossier_courant = Path(__file__).parent
    
    # On pointe vers les fichiers (suppose qu'ils sont dans le même dossier)
    path_serveur = dossier_courant / "code" / "serveur.py"
    path_client = dossier_courant / "code" /"client.py"

    # On récupère l'exécutable python actuel (ex: /usr/bin/python3 ou venv/bin/python)
    python_exe = sys.executable

    print(f"--- Lancement automatique ---")
    print(f"OS détecté : {systeme}")
    print(f"Python utilisé : {python_exe}")
    print(f"Dossier cible : {dossier_courant}")

    if not path_serveur.exists() or not path_client.exists():
        print("\n[ERREUR] Impossible de trouver serveur.py ou client.py dans ce dossier.")
        return

    if systeme == "Windows":
        # start "Titre" cmd /k command
        # Les guillemets vides "" après start sont pour le Titre de la fenêtre (requis si le chemin contient des espaces)
        cmd_serv = f'start "Serveur" cmd /k "{python_exe} "{path_serveur}""'
        cmd_cli = f'start "Client" cmd /k "{python_exe} "{path_client}""'
        
        subprocess.Popen(cmd_serv, shell=True)
        time.sleep(1)
        subprocess.Popen(cmd_cli, shell=True)
        
    elif systeme == "Linux":
        # On essaie plusieurs terminaux courants
        terminaux = [
            ['gnome-terminal', '--', python_exe, str(path_serveur)],
            ['xterm', '-e', python_exe, str(path_serveur)],
            ['konsole', '-e', python_exe, str(path_serveur)]
        ]
        
        succes = False
        for term_cmd in terminaux:
            try:
                # Lancement Serveur
                subprocess.Popen(term_cmd)
                time.sleep(1)
                
                # Adaptation commande client pour le même terminal
                term_cmd[-1] = str(path_client)
                subprocess.Popen(term_cmd)
                succes = True
                break
            except FileNotFoundError:
                continue
        
        if not succes:
            print("Aucun terminal compatible trouvé (gnome-terminal, xterm, konsole).")
            
    elif systeme == "Darwin": # macOS
        # Utilisation d'AppleScript pour dire au Terminal d'exécuter la commande
        # Cela évite d'ouvrir le fichier dans l'éditeur de texte
        script_serv = f'tell application "Terminal" to do script "{python_exe} {path_serveur}"'
        script_cli = f'tell application "Terminal" to do script "{python_exe} {path_client}"'
        
        subprocess.Popen(['osascript', '-e', script_serv])
        time.sleep(1)
        subprocess.Popen(['osascript', '-e', script_cli])

    print("Terminaux lancés.")

if __name__ == "__main__":
    lancer_app()