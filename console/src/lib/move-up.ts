export function moveUp<T>(list: T[], index: number): T[] {
  if (index <= 0) return list;
  const next = [...list];
  [next[index - 1], next[index]] = [next[index], next[index - 1]];
  return next;
}
