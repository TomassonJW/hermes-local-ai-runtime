/**
 * Consumer-side TypeScript sketch. Persist vectors without model filenames.
 * A different space_id means re-embed. The runtime never sees this store.
 */

export type VectorRecord = {
  id: string;
  vector: number[];
  dimensions: number;
  normalisation: "l2";
  space_id: string;
};

const FORBIDDEN = ["model", "model_artifacts", "checkpoint", "gguf", "engine"];

export function assertConsumerRecord(record: VectorRecord): void {
  for (const key of Object.keys(record)) {
    if (FORBIDDEN.includes(key)) {
      throw new Error(`consumer record must not store ${key}`);
    }
  }
  const dumped = JSON.stringify(record).toLowerCase();
  if (dumped.includes("gguf") || dumped.includes(".onnx")) {
    throw new Error("consumer record must not store a model filename");
  }
}

export function cosine(left: number[], right: number[]): number {
  let num = 0;
  let leftNorm = 0;
  let rightNorm = 0;
  for (let i = 0; i < left.length; i += 1) {
    num += left[i] * right[i];
    leftNorm += left[i] * left[i];
    rightNorm += right[i] * right[i];
  }
  const den = Math.sqrt(leftNorm) * Math.sqrt(rightNorm);
  return den === 0 ? 0 : num / den;
}
