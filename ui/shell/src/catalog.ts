export type InputKind =
  | 'text'
  | 'texts'
  | 'query-docs'
  | 'file'
  | 'file-question'
  | 'two-files'

export interface FnDef {
  id: string
  title: string
  blurb: string
  input: InputKind
  accept?: string
  timeoutMs: number
}

export const FUNCTIONS: FnDef[] = [
  {
    id: 'document.extract_structured',
    title: 'Lire une facture',
    blurb: 'Numéro et montant depuis un PDF ou une photo.',
    input: 'file',
    accept: 'application/pdf,image/png,image/jpeg,image/webp',
    timeoutMs: 90000,
  },
  {
    id: 'document.ocr',
    title: 'Lire le texte d’une image',
    blurb: 'OCR français / anglais, page par page.',
    input: 'file',
    accept: 'application/pdf,image/png,image/jpeg,image/webp',
    timeoutMs: 90000,
  },
  {
    id: 'document.text_extract',
    title: 'Extraire le texte d’un PDF',
    blurb: 'Texte natif, sans OCR. Signale un PDF image.',
    input: 'file',
    accept: 'application/pdf',
    timeoutMs: 20000,
  },
  {
    id: 'vision.analyze',
    title: 'Question sur une image',
    blurb: 'Le modèle visuel répond à ta question. Quelques secondes.',
    input: 'file-question',
    accept: 'image/png,image/jpeg,image/webp',
    timeoutMs: 180000,
  },
  {
    id: 'vision.detect_objects',
    title: 'Repérer des objets colorés',
    blurb: 'Borné aux gros aplats rouge / bleu de test.',
    input: 'file',
    accept: 'image/png,image/jpeg,image/webp',
    timeoutMs: 15000,
  },
  {
    id: 'vision.compare',
    title: 'Comparer deux images',
    blurb: 'Similarité de copie, pas une compréhension sémantique.',
    input: 'two-files',
    accept: 'image/png,image/jpeg,image/webp',
    timeoutMs: 15000,
  },
  {
    id: 'text.generate',
    title: 'Écrire un texte',
    blurb: 'Petit modèle local. Pas un égal des grands clouds.',
    input: 'text',
    timeoutMs: 120000,
  },
  {
    id: 'text.embed',
    title: 'Transformer en vecteurs',
    blurb: 'Tu stockes les vecteurs. Le runtime ne garde pas de base.',
    input: 'texts',
    timeoutMs: 120000,
  },
  {
    id: 'search.rerank',
    title: 'Reclasser des résultats',
    blurb: 'Une requête, plusieurs passages, un nouvel ordre.',
    input: 'query-docs',
    timeoutMs: 120000,
  },
  {
    id: 'audio.transcribe',
    title: 'Transcrire un audio',
    blurb: 'Whisper batch. Les identifiants type SYN-0042 restent peu fiables.',
    input: 'file',
    accept: 'audio/wav,audio/mpeg,audio/ogg,audio/webm,audio/*',
    timeoutMs: 180000,
  },
]

export const PROFILE_LABELS: Record<string, string> = {
  fast: 'Rapide',
  balanced: 'Équilibré',
  accurate: 'Précis',
}

export const NAV = [
  { path: '/', name: 'Essayer' },
  { path: '/overview', name: 'Vue d’ensemble' },
  { path: '/jobs', name: 'Jobs' },
  { path: '/resources', name: 'Ressources' },
  { path: '/capabilities', name: 'Fonctions' },
  { path: '/models', name: 'Modèles' },
  { path: '/evaluations', name: 'Mesures' },
  { path: '/updates', name: 'Mises à jour' },
  { path: '/settings', name: 'Réglages' },
]
