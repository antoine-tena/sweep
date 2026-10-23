# Sweep

Trouve ce qui encombre la RAM et le swap (agents oubliés, serveurs orphelins) et propose quoi tuer, sous Linux, WSL, macOS et Windows.

## Démarrage rapide

Après le clone, depuis la racine du dépôt (prérequis : [uv](https://docs.astral.sh/uv/)) :

```sh
uv tool install kiln-cli   # une fois par poste
kiln install
```

Puis lancer l'outil : `cd backend && uv run sweep --help`, ou l'installer sur le poste par
`uv tool install --editable backend`.

## Équipe

- [@antoine-tena](https://github.com/antoine-tena)

## Organisation

- `backend/` : l'outil en ligne de commande `sweep`.
- [`CLAUDE.md`](CLAUDE.md) et [`.claude/rules/kiln/`](.claude/rules/kiln/) : la charte du code
  et la façon de travailler, pour les humains comme pour les agents.
- `.vscode/` : réglages et extensions recommandées, partagés par toute l'équipe.

Le projet est généré et tenu à jour par [kiln](https://github.com/antoine-tena/kiln). Changer un
paramètre (équipe, frameworks, podman…) : `kiln set <clé>=<valeur>`, sur une branche.

## Installation

Prérequis : ceux du démarrage rapide.
`kiln install` installe les dépendances (backend) et active les garde-fous du
commit (pre-commit, dont le refus de commiter sur `main` ou `develop`). On peut la relancer sans
risque.

## Lancer le projet

```sh
cd backend && uv run sweep --help
uv tool install --editable backend   # depuis la racine : la commande sur tout le poste
```

## Ce que sweep arrête

`sweep` ne fait que montrer. Il range ce qu'il trouve en deux niveaux :

- **Sûr** : une preuve dit que le process ne peut plus servir. `sweep --kill` arrête ceux-là,
  après confirmation (`--yes` pour ne pas la demander, `--dry-run` pour simuler).
- **À vérifier** : peut-être encore utilisé. Jamais arrêté par `--kill` seul ; on désigne celui
  qu'on veut arrêter par `sweep --kill --pid N`.

Les preuves exigées pour « sûr » (sous macOS, les serveurs MCP restent à vérifier, faute de lire
leur canal ; sous Windows, qui ne rattache pas les orphelins, tout reste à vérifier) :

| Reste | Sûr si… | Sinon, à vérifier si… |
|---|---|---|
| Serveur MCP | son lanceur est mort (recueilli par `init` ou `systemd --user`) **et** plus aucun process ne tient le canal par lequel l'agent lui parlait | détaché sans canal (lancé à part exprès ?) |
| Agent (claude, agy…) | interactif, sans terminal, lanceur mort, inactif | inactif depuis `--idle-hours` (3 h), ou même conversation ouverte deux fois |
| Agent suspendu (Ctrl+Z) | un autre agent tourne dans son terminal : il a été oublié derrière | seul dans son terminal (`fg` le reprend) |
| Serveur de dev | dossier supprimé, sans terminal, lanceur mort | dossier supprimé mais encore attaché |

Jamais candidats : les process d'un autre utilisateur, sweep et ses ancêtres (le terminal,
l'agent qui le lance), un process dont le parent vit encore et lui parle, un dossier vu dans un
conteneur. Avant d'arrêter, sweep vérifie que le pid n'a pas été réattribué ; il envoie SIGTERM,
puis SIGKILL à ceux qui l'ignorent.

## Mettre à jour

Sur une branche dédiée (`chore/kiln-update`), avec un arbre propre :

```sh
kiln update            # mises à jour compatibles
kiln update --major    # y compris les versions majeures
```

Elle rapporte les évolutions du modèle (charte, outillage, configuration) sans écraser les
modifications locales, met à jour les dépendances, puis lance les contrôles. Relire le diff,
puis fusionner la branche dans `develop`. Avec Claude Code, la skill `kiln:update` fait tout :
l'outil kiln, puis le dépôt.

## Vérifier le code

```sh
kiln check
```

Ruff, mypy et pytest pour chaque projet Python, puis la charte (`charter`).

## Mettre à jour

Sur une branche dédiée, avec un arbre propre : `kiln update` (mises à jour compatibles) ou
`kiln update --major` (versions majeures comprises). La commande rapporte les évolutions de kiln
sans écraser les modifications locales, met à jour les dépendances, puis lance les contrôles.
Avec Claude Code, le skill `/kiln:update` fait tout : l'outil kiln, puis le dépôt.

## Suivi du travail

Ce qui reste à faire est dans [`docs/backlog/`](docs/backlog/) : `backlog.md` (les tickets, par
priorité), `done.md` (ceux qui sont faits), `rejected.md` (ce qui a été refusé) et `urgent.md` (ce que seul un humain peut faire).

## Contribuer

1. Créer une branche depuis `develop` : `feat/…`, `fix/…` ([BRANCHES]).
2. Respecter la charte ([`.claude/rules/kiln/`](.claude/rules/kiln/), [`CLAUDE.md`](CLAUDE.md)).
3. Fusionner la branche dans `develop` (`git merge --no-ff`, puis push), sans attendre
   d'approbation : skill `/kiln:merge` avec Claude Code. Une pull request reste possible pour
   demander un avis. On ne commite jamais directement sur `main` ou `develop`.
