export const ROUND_COUNT = 5;
export const ROUND_SECONDS = 60;
export function normalizeGuess(value) {
  return String(value || '')
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\s\p{P}\p{S}]/gu, '');
}
export function matchesGuess(puzzle, value) {
  const guess = normalizeGuess(value);
  return (
    guess.length > 0 &&
    [puzzle.answer, ...puzzle.aliases].some((alias) => normalizeGuess(alias) === guess)
  );
}
export function roundScore(seconds, hintCount) {
  return Math.max(
    20,
    40 + Math.ceil(Math.max(0, Math.min(ROUND_SECONDS, seconds))) - 20 * hintCount
  );
}
export function shuffled(items, random = Math.random) {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
export function createGame(puzzles, random = Math.random) {
  let deck = [],
    index = 0,
    results = [],
    hints = 0,
    resolved = false;
  return {
    start() {
      deck = shuffled(puzzles, random).slice(0, ROUND_COUNT);
      index = 0;
      results = [];
      hints = 0;
      resolved = false;
      return this.current;
    },
    get current() {
      return deck[index];
    },
    get number() {
      return index + 1;
    },
    get total() {
      return deck.length;
    },
    get results() {
      return [...results];
    },
    get score() {
      return results.reduce((sum, r) => sum + r.score, 0);
    },
    get resolved() {
      return resolved;
    },
    get hints() {
      return hints;
    },
    hint() {
      if (resolved || hints >= this.current.hints.length) return null;
      return this.current.hints[hints++];
    },
    guess(value, seconds) {
      if (resolved) return null;
      if (!matchesGuess(this.current, value)) return false;
      return this.resolve('correct', seconds);
    },
    resolve(status, seconds = 0) {
      if (resolved) return null;
      if (!['correct', 'skip', 'timeout'].includes(status)) throw new Error('Unknown round status');
      resolved = true;
      const result = {
        answer: this.current.answer,
        status,
        score: status === 'correct' ? roundScore(seconds, hints) : 0,
        hints,
      };
      results.push(result);
      return result;
    },
    next() {
      if (!resolved) return false;
      if (index + 1 >= deck.length) return false;
      index++;
      hints = 0;
      resolved = false;
      return true;
    },
  };
}
