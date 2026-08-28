# Hermes Local AI Runtime

Un runtime local, sobre en ressources et piloté par capacités pour Hermes et les autres applications.

> **État :** candidat source public. Baseline produit `0.1.0`, API `0.2.0-dev`.
> Un noyau de jobs en loopback et un installateur préfixe existent. Ce n'est
> **pas** un programme du quotidien, **pas** un support production, et **pas**
> un substitut aux grands modèles cloud.

Hermes Local AI Runtime doit devenir le noyau IA local partagé de l’environnement Hermes : un seul service où les logiciels peuvent demander de l’OCR, de la compréhension documentaire, de l’extraction structurée, des embeddings, du reranking, de la vision générale, de l’analyse d’objets ou d’images et de la transcription audio — puis, plus tard, des modèles de langage plus importants.

Les logiciels consommateurs ne dépendent pas d’un nom de modèle. Ils appellent des capacités versionnées comme `vision.analyze`, `document.ocr`, `text.extract_structured`, `text.embed`, `search.rerank` ou `audio.transcribe`. Le runtime choisit le moteur, le modèle approuvé, le preset, le worker et la cible d’exécution selon des politiques explicites de qualité, de confidentialité et de ressources.

## Ce que signifie « noyau IA »

Il s’agit d’un **noyau de capacités et d’orchestration**, pas d’un noyau système privilégié et pas d’un modèle universel.

Il centralise les contrats d’API, le registre des modèles et moteurs, le routage par capacité, le chargement et le déchargement, les quotas/files/limites de ressources, la provenance, les benchmarks et les intégrations Hermes/OpenAI-compatible/MCP.

Il ne centralise pas les bases métier des applications. Chaque logiciel reste propriétaire de ses données, de ses règles, de ses écritures et de ses décisions finales.

## Principes

- **Capacités avant modèles.** Une application demande un résultat, pas un checkpoint.
- **Local d’abord, sans dogme.** Un repli distant ne peut exister que si la politique du consommateur l’autorise.
- **Spécialistes avant généralistes.** OCR, détection, recherche vectorielle, reranking et audio utilisent des moteurs spécialisés lorsque c’est plus fiable ou plus léger.
- **Admission avant exécution.** Aucune tâche IA ne doit saturer silencieusement le serveur Hermes.
- **Preuve avant promotion.** Un modèle reste candidat tant qu’il n’a pas passé les gates de licence, compatibilité, qualité, mémoire, latence et régression.
- **Aucune écriture cachée.** Le runtime calcule ; l’application consommatrice décide et écrit.
- **Moteurs remplaçables.** L’API native est complétée par une façade OpenAI-compatible et une intégration MCP optionnelle.
- **GPU futur sans réécriture.** Les workers CPU sont la première cible ; les workers GPU et distants garderont les mêmes contrats.

## Cible matérielle initiale

Le premier déploiement réel est la VM Ubuntu Hermes existante : 8 vCPU sur un hôte AMD Ryzen 9 7900, 16 Gio de RAM dans la VM, aucun GPU, plusieurs autres applications déjà actives, accès local ou via tailnet sans écoute publique par défaut.

Le profil initial garde une réserve mémoire forte, n’autorise qu’une inférence générative lourde à la fois, charge les modèles importants à la demande et considère l’usage soutenu du swap comme un refus d’admission raté, pas comme un fonctionnement normal.

## Vision locale : objectif réaliste

Un petit VLM CPU ne doit pas être présenté comme équivalent à tous les meilleurs modèles cloud. Il peut néanmoins remplacer une grande partie des usages visuels bornés : décrire une capture, lire une interface simple, classer une image, extraire des champs, faire un premier diagnostic, reconnaître des objets ou retrouver des images avec des modèles spécialisés, et traiter localement des documents confidentiels.

Les tâches complexes, ambiguës, multi-images, très fines ou à fort enjeu doivent pouvoir être signalées comme insuffisamment fiables et suivre une politique de repli. Le benchmark décide ; le marketing ne décide pas.

## Ordre de lecture

1. [`AGENTS.md`](AGENTS.md)
2. [`provenance/COMPILATION-MANIFEST.yml`](provenance/COMPILATION-MANIFEST.yml)
3. [`product/00-index.md`](product/00-index.md)
4. [`architecture/00-index.md`](architecture/00-index.md)
5. [`GATES.md`](GATES.md)
6. [`STATE.md`](STATE.md)
7. [`HANDOFF.md`](HANDOFF.md)

L’anglais est la langue canonique du dépôt public. Le présent fichier maintient l’intention en français ; les identifiants techniques restent en anglais.

## Licence

Le code et la documentation originaux sont sous Apache License 2.0. Les moteurs, modèles, jeux de données et composants téléchargés conservent leurs licences propres. Voir [`LICENSE`](LICENSE), [`NOTICE`](NOTICE) et [`registry/LICENSE-POLICY.md`](registry/LICENSE-POLICY.md).
