# streamdock_autocad

Plugin Stream Dock (Mirabox / logiciel HotSpot) pour piloter AutoCAD sous Windows.

## Actions

| Action  | Rôle |
|---------|------|
| Macro   | Exécute un preset ou une suite de commandes AutoCAD (une commande par ligne, ligne vide = Entrée). Les presets perso s'enregistrent depuis le panneau de la touche. |
| Bascule | Active/désactive ORTHO, accrochage objets, accrochage grille, grille, épaisseurs. La touche reflète l'état réel d'AutoCAD. |
| Calque  | Rend un calque courant (le crée si besoin). La touche affiche le calque actif. |
| État    | Affiche le calque courant, le nom du dessin ou les modes actifs. |
| Drawflow | Envoie le dessin ouvert (enregistré) à un module Drawflow via son API locale, nom du projet = nom du dessin. |
| Bloc    | Insère un bloc du dessin au point cliqué, échelle et rotation fixes ou demandées. Liste des blocs dans le panneau. |
| Imprimer | Imprime la présentation courante avec une mise en page nommée, ou l'exporte en PDF (nom du dessin) dans un dossier. |
| Molette | Sur un bouton rotatif : zoom (appui = zoom étendu), calque courant (appui = calque 0) ou annuler/rétablir (appui = régénérer). |

## Fonctionnement

Le plugin est un exécutable lancé par Stream Dock, qui lui parle en WebSocket JSON. Côté AutoCAD, il passe par COM
(`AutoCAD.Application`) : `SendCommand` pour les commandes, `GetVariable`/`SetVariable` pour l'état. AutoCAD doit être ouvert ;
il n'a pas besoin d'avoir le focus.

Les presets livrés sont dans `com.tmbk.streamdock.autocad.sdPlugin/presets/`. Les presets perso vont dans
`%APPDATA%\tmbk\streamdock-autocad\presets\` et survivent aux mises à jour du plugin.

Écrire les commandes avec le préfixe `_.` (indépendant de la langue, ignore les redéfinitions) et la variante `-` des commandes
qui ouvrent une boîte de dialogue (`_.-LAYER`, `_.-BLOCK`, `_.-INSERT`).

### Étapes AutoLISP

Une étape `@lisp fichier.lsp` charge ce fichier avant la suite. Les fichiers sont cherchés dans
`%APPDATA%\tmbk\streamdock-autocad\presets\lisp\` (perso, prioritaire) puis dans `presets/lisp/` du plugin.
Le preset « Cube + bloc » utilise `cube.lsp` : il demande le nom, la taille et le point d'insertion dans la ligne de commande,
dessine le cube, le convertit en bloc et l'insère.

```json
{ "name": "Cube + bloc", "steps": ["@lisp cube.lsp", "(c:tmbk-cube)"] }
```

### Drawflow

La touche Drawflow lit le port et le jeton dans `%APPDATA%\ch.drawflow.desktop\integrations.json` (API locale activée dans
Paramètres → API locale de Drawflow), ouvre une connexion WebSocket le temps de la commande et appelle `feature.run` avec le
chemin du dessin dans `files`. Le formulaire s'ouvre rempli dans Drawflow ; les champs manquants (dossier de sortie) se
complètent là-bas.

### Erreurs et mises à jour

Une action qui échoue affiche le triangle d'alerte, écrit le message dans la ligne de commande AutoCAD (préfixe « Stream Dock : »)
et dans le panneau de la touche. Le plugin vérifie la dernière release GitHub toutes les six heures ; une version plus récente
apparaît en haut du panneau de chaque touche avec un lien vers la page de téléchargement.

## Prérequis (poste Windows)

- Stream Dock installé
- AutoCAD (version complète, pas LT : LT n'expose pas COM)
- Python 3.12+ et [uv](https://docs.astral.sh/uv/)

## Build et installation

```powershell
scripts\build.ps1     # uv sync + PyInstaller -> plugin.exe dans le .sdPlugin + dist\<plugin>.zip
scripts\install.ps1   # copie dans %APPDATA%\HotSpot\StreamDock\plugins et relance Stream Dock
```

## Release et installation depuis Drawflow

Un tag `vX.Y.Z` déclenche `release.yml` : build Windows, smoke test, zip puis GitHub Release avec l'asset
`com.tmbk.streamdock.autocad.sdPlugin.zip`. Le zip contient le dossier `com.tmbk.streamdock.autocad.sdPlugin/` à la racine,
le format que l'installateur de Drawflow dézippe dans Stream Dock.

```bash
uv run python scripts/version.py bump 0.2.0   # pyproject + manifest
git commit -am "chore: release 0.2.0" && git tag v0.2.0 && git push --tags
```

URL stable de la dernière version :
`https://github.com/pepito2t/streamdock_autocad/releases/latest/download/com.tmbk.streamdock.autocad.sdPlugin.zip`
(ou `.../releases/download/vX.Y.Z/...` pour une version précise). La CI (`ci.yml`) produit le même zip en artefact sur chaque PR.

Debug : `http://localhost:23519/` liste les plugins chargés. Logs du plugin : `<dossier du plugin>\logs\plugin.log`.

## Développement

```bash
uv sync --group dev
uv run pytest
uv run python scripts/make_icons.py   # régénère les icônes (Pillow)
```

Hors Windows, le plugin utilise un bridge AutoCAD simulé (`src/bridge/autocad_fake.py`) : les tests tournent partout,
le test réel se fait sur le poste Windows.

## Structure

```
com.tmbk.streamdock.autocad.sdPlugin/   manifest, icônes, property inspectors, presets livrés
src/core/                               SDK Python officiel Mirabox (non modifié)
src/bridge/                             accès AutoCAD : protocole, impl COM, impl simulée
src/macros/                             modèle de macro, store de presets, exécution
src/actions/                            une classe par action (nom de fichier = dernier segment de l'UUID)
tests/                                  pytest, bridge simulé
scripts/                                build/install Windows, génération d'icônes
```
